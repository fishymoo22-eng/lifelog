from pathlib import Path
import pandas as pd
from datetime import datetime
import re

import streamlit as st
import streamlit.components.v1 as components
import psycopg
import pytz
import random


def main():
    """
    Log my life!
    """

    # record run time in relevant timezone
    user_timezone = pytz.timezone(st.context.timezone)
    run_timestamp = datetime.now(user_timezone).strftime("%Y-%m-%d %I:%M:%S %p")

    # initialize database connection
    conn = psycopg.connect(st.secrets["database"]["url"])

    # configure and render app
    configure_app()
    st.title("Life Log")
    render_aquarium(conn)
    render_things_to_remember(run_timestamp, conn)
    render_dreams(run_timestamp, conn)
    render_activity_roll(run_timestamp, conn)
    render_activities(run_timestamp, conn)
    render_journal(run_timestamp, conn)
    render_mood(run_timestamp, conn)
    configure_user_options(run_timestamp, conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


def configure_app():
    """
    Configure app display settings. 
    """

    # remove excess padding from bottom of page
    st.markdown(
        """
        <style>
            .block-container {
                padding-bottom: 0rem;
                padding-top: 1rem;
            }
        </style>
        """,
        unsafe_allow_html = True,
    )


def render_aquarium(conn):
    """
    Render section: Aquarium.
    This section displays a nice aquarium.
    """
    
    # display header: aquarium!
    st.header("Aquarium")

    cursor = conn.cursor()

    # define random seed 
    if "aquarium_seed" not in st.session_state:
        st.session_state.aquarium_seed = random.randint(0, 999999)
    random.seed(st.session_state.aquarium_seed)

    # pull in fish configuration from database
    fish_config_pd = pd.read_sql_query("""
        select * 
        from fish_config 
    """, conn)
    fish_config = fish_config_pd.to_dict("records")
    
    # build dictonary with svg of each fish type 
    fish_shape_svg = {
        "Baby": Path(f"aquarium_shapes/fish/fish_baby.svg").read_text(),
        "Child": Path(f"aquarium_shapes/fish/fish_child.svg").read_text(),
        "Teen": Path(f"aquarium_shapes/fish/fish_teen.svg").read_text(),
        "Adult": Path(f"aquarium_shapes/fish/fish_adult.svg").read_text()
    }
    # finalize fish configuration
    fish_config_w_daddys = {}
    for fish_dict in fish_config:
        fish_dict_copy = fish_dict.copy()

        # define randomized values
        fish_dict_copy["top1"] = random.randint(5, 70)
        fish_dict_copy["top2"] = random.randint(5, 70)
        fish_dict_copy["delay"] = random.randint(-40, 40)
        fish_dict_copy["speed"] = random.randint(35, 50)

        # for later generation level 0 babies, add a daddy
        if fish_dict_copy["generation"] > 0 and fish_dict_copy["level"] == 0:
            # define daddy features based on baby
            daddy_dict = fish_dict_copy.copy()

            # modify certain features
            daddy_dict["fish_id"] = f"dad-{fish_dict_copy['fish_id']}"
            daddy_dict["fish_name"] = f"{fish_dict_copy['fish_name']}'s Daddy"
            daddy_dict["generation"] = fish_dict_copy["generation"] + 1
            daddy_dict["level"] = 19

            # update baby fish positioning based on daddy
            fish_dict_copy["top1"] = fish_dict_copy["top1"] + 5
            fish_dict_copy["top2"] = fish_dict_copy["top2"] + 5
            fish_dict_copy["delay"] = fish_dict_copy["delay"] + 0.7
            fish_dict_copy["speed"] = fish_dict_copy["speed"]

            fish_config_w_daddys[str(daddy_dict["fish_id"])] = daddy_dict

        # add dictionary to final fish config list
        fish_config_w_daddys[str(fish_dict_copy["fish_id"])] = fish_dict_copy

    # now loop through all fish in final config 
    for fish_id, fish_dict in fish_config_w_daddys.items():
        # determine fish type and size based on level
        if fish_dict["level"] < 5:
            fish_type = "Baby"
        elif fish_dict["level"] < 10:
            fish_type = "Child"
        elif fish_dict["level"] < 15:
            fish_type = "Teen"
        else:
            fish_type = "Adult"

        fish_dict["fish_age"] = fish_type

        # the size starts at 0.335, then adds 0.035 up until level 19, where it reaches 1
        fish_size = 0.335 + 0.035 * fish_dict["level"]
        
        # grab raw fish svg 
        fish_svg_text = fish_shape_svg[fish_type]
    
        # remove light body for generation 0
        if fish_dict["generation"] == 0:
            fish_svg_text = re.sub(
                r'<path\b(?=[^>]*\bid="body-light")[^>]*/>',
                '',
                fish_svg_text
            )

        # remove individual tail-line paths for generation 0 and 1
        if fish_dict["generation"] <= 1:
            fish_svg_text = re.sub(
                r'<path\b(?=[^>]*\bid="tail-line-[^"]+")[^>]*/>',
                '',
                fish_svg_text
            )

        # remove individual scale paths generations 0/1/2
        if fish_dict["generation"] <= 2:
            fish_svg_text = re.sub(
                r'<path\b(?=[^>]*\bid="scale-[^"]+")[^>]*/>',
                '',
                fish_svg_text
            )

        # map svg colors to new colors
        color_map = {
            "#ff7a00": fish_dict["base_color"], 
            "#ffa95a": fish_dict["light_accent_color"], 
            "#e66e00": fish_dict["dark_accent_color"],
            "#ff912d": fish_dict["gradient_color_1"],
            "#f2be7f": fish_dict["gradient_color_2"],
            "#e6d4a4": fish_dict["gradient_color_3"],
        }

        for old_color, new_color in color_map.items():
            fish_svg_text = fish_svg_text.replace(old_color, new_color)

        # map svg ids to unique ids per fish
        fish_id = fish_dict["fish_id"]
        id_map = {
            '"fish-body"': f'"f{fish_id}-fish-body"',
            '"body"': f'"f{fish_id}-body"',
            '"body-light"': f'"f{fish_id}-body-light"',
            '"fish-tail-base"': f'"f{fish_id}-fish-tail-base"',
            '"fish-tail"': f'"f{fish_id}-fish-tail"',
            '"eye-white"': f'"f{fish_id}-eye-white"',
            '"pupil"': f'"f{fish_id}-pupil"',
            '"gill-1"': f'"f{fish_id}-gill-1"',
            '"gill-2"': f'"f{fish_id}-gill-2"',
            '"mouth"': f'"f{fish_id}-mouth"',
            '"pectoral-fin"': f'"f{fish_id}-pectoral-fin"',
            'linearGradient32': f'f{fish_id}linearGradient32',
        }

        for old_id, new_id in id_map.items():
            fish_svg_text = fish_svg_text.replace(old_id, new_id)

        # save finalized svg text
        fish_dict["svg"] = f"""
            <div class="fish-container"
                style="
                --top1:{fish_dict['top1']}%;
                --top2:{fish_dict['top2']}%;
                --speed:{fish_dict['speed']}s; 
                --fin-speed:{fish_size}s;
                --delay:{fish_dict['delay']}s;  
                --size:{fish_size};">

                {fish_svg_text}

            </div>
        """

    # define bubble html
    bubble_html = ""
    
    for i in range(30):
        bubble_html += f"""
        <div class="bubble"
            style="
                --left:{random.randint(0,100)}%;
                --size:{random.uniform(6,20):.1f}px;
                --duration:{random.uniform(4,10):.1f}s;
                --delay:{random.uniform(-10,0):.1f}s;
                --drift:{random.randint(-25,25)}px;
            ">
        </div>
        """

    # read kelp svg 
    kelp_long_svg = Path("aquarium_shapes/kelp/kelp_long.svg").read_text()
    kelp_short_1_svg = Path("aquarium_shapes/kelp/kelp_short_1.svg").read_text()
    kelp_short_2_svg = Path("aquarium_shapes/kelp/kelp_short_2.svg").read_text()

    # define kelp layout
    kelp_config = [
        {"svg": kelp_short_1_svg, "left": 30, "scale": 1},
        {"svg": kelp_long_svg, "left": 40, "scale": 1},
        {"svg": kelp_short_2_svg, "left": 50, "scale":1},
    ]

    # generate kelp html
    kelp_html = ""

    for kelp in kelp_config:
        kelp_html += f"""
        <div class="kelp"
            style="
                --left:{kelp["left"]}px;
                --scale:{kelp["scale"]};
            ">
            {kelp["svg"]}
        </div>
        """

    # define html content 
    content = f"""
    <style>

    body {{
        margin:0;
        overflow:hidden;
    }}

    .aquarium {{
        position: relative;
        width:100%;
        height:400px;
        background:
        linear-gradient(
            to bottom,
            #a9d8ef,
            #7bb8df
        );
        overflow:hidden;
    }}
    .floor {{
        position:absolute;

        bottom:0;
        left:0;

        width:100%;
        height:60px;
        background:
        linear-gradient(
            to bottom,
            #f7edc8,
            #dfcf9b
        );

        z-index:1;
    }}


    .floor::before {{
        content:"";

        position:absolute;

        top:-10px;
        left:0;

        width:100%;
        height:20px;

        background:
            radial-gradient(
                ellipse,
                rgba(255,255,255,.35) 0%,
                transparent 70%
            );

        opacity:.5;
    }}

    .fish-container {{
        position: absolute;
        left: -30%;

        animation-name: swim;
        animation-timing-function: linear;
        animation-iteration-count: infinite;
        animation-fill-mode: both;

        animation-duration: var(--speed, 20s);
        animation-delay: var(--delay, 0s);

        top: var(--depth, 20%);
        transform: scale(var(--size, 1));
        
        z-index:5;
    }}

    .bubble {{
        position: absolute;

        left: var(--left);
        bottom: 0px;

        width: var(--size);
        height: var(--size);

        border-radius: 50%;

        background: transparent;
        border: 1px solid rgba(255,255,255,.45);

        box-shadow:
            inset 2px 2px 2px rgba(255,255,255,.2);

        animation: rise var(--duration) linear infinite;
        animation-delay: var(--delay);

        pointer-events: none;

        z-index:1;
    }}
    .bubble::after {{
        content: "";

        position: absolute;

        width: 20%;
        height: 20%;

        top: 20%;
        left: 20%;

        border-radius: 50%;

        background: rgba(255,255,255,.8);

        filter: blur(1px);
    }}

    svg {{
        width:130px;
        height:auto;
    }}
    
    .kelp-container {{
        position:absolute;
        inset:0;

        z-index:2;
    }}

    .kelp {{
        position:absolute;

        bottom:10px;
        left:var(--left);

        height:200px;

        transform:
            scale(var(--scale));

        transform-origin:bottom center;
    }}

    .kelp svg {{
        height:100%;
        width:auto;
    }}

    /* animate tail if SVG contains fish-tail in id */
    [id$="fish-tail"] {{
        transform-box:fill-box;
        transform-origin:left center;

        animation:
            tail-wag var(--fin-speed, .7s) ease-in-out infinite alternate;
            transform: rotate(10deg);
    }}

    /* animate fin */
    [id$="pectoral-fin"] {{
        transform-box:fill-box;
        transform-origin:top center;

        animation:
            fin-flutter var(--fin-speed, .7s) ease-in-out infinite alternate;
    }}

    /* animate bubbles */
    @keyframes rise {{
        from {{
            transform: translate(0, 0);
            opacity: 1;
        }}

        to {{
            transform: translate(var(--drift),-380px);
            opacity: 1;
        }}
    }}

    /* animate fish swimming */
    @keyframes swim {{
        0% {{
            left:-140px;
            top: var(--top1);
            transform:scaleX(-1) scale(var(--size));
        }}

        45% {{
            left:100%;
            top: var(--top1);
            transform:scaleX(-1) scale(var(--size));
        }}

        50% {{
            left:100%;
            top: var(--top2);
            transform:scaleX(1) scale(var(--size));
        }}

        95% {{
            left:-140px;
            top: var(--top2);
            transform:scaleX(1) scale(var(--size));
        }}

        100% {{
            left:-140px;
            top: var(--top1);
            transform:scaleX(-1) scale(var(--size));
        }}
    }}

    /* animate tail/fin wagging */
    @keyframes tail-wag {{
        from {{
            transform:rotate(12deg);
        }}
        to {{
            transform:rotate(-12deg);
        }}
    }}

    @keyframes fin-flutter {{
        from {{
            transform:rotate(-10deg);
        }}
        to {{
            transform:rotate(15deg);
        }}
    }}

    </style>
    
    <div class="aquarium">

        <!-- insert bubbles -->
        {bubble_html}

        <!-- ocean floor -->
        <div class="floor">
        </div>

        <!-- insert kelp -->
        <div class="kelp-container">
            {kelp_html}
        </div>

        {
            " ".join([fish_dict["svg"] for fish_dict in fish_config_w_daddys.values()])
        }

    </div>
    """

    # display aquarium
    components.html(content, height=400, scrolling=True)

    # display table with fish attributes
    fish_df = pd.DataFrame(fish_config_w_daddys.values())
    fish_df = fish_df.sort_values(["fish_id"], ignore_index = True)
    fish_df = fish_df[["fish_name", "fish_mapping", "fish_age", "generation", "level"]]
    fish_df = fish_df.rename(columns={
        "fish_name": "Name",
        "fish_mapping": "Mapping",
        "fish_age": "Age",
        "generation": "Generation",
        "level": "Level"
    })
    st.table(fish_df)

    cursor.close()

def render_things_to_remember(run_timestamp, conn):
    """
    Render section: Things to Remember.
    This section keeps a running, editable list of things to remember.
    """
    
    # display header: log my things to remember!
    st.header("Things to Remember")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        if "things_to_remember_update" not in st.session_state:
            st.session_state["things_to_remember_update"] = False

        with st.form(key = "things_to_remember_form", border=False):
            # read things to remember from sql
            things_to_remember_curr = pd.read_sql_query("""
                select thing_to_remember 
                from things_to_remember 
                order by entry_time
            """, conn)

            # display with st.data_editor, which allows us to remove or edit items dynamically
            things_to_remember_new = st.data_editor(
                things_to_remember_curr,
                num_rows = "dynamic",
                column_config = {
                    "thing_to_remember": st.column_config.TextColumn(
                        "Thing to Remember",
                        width = 275
                    )
                }
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Save Changes")

        if submit_button:
            # get updated list of things to remember and date
            things_to_remember = [
                (run_timestamp, thing_to_remember)
                for thing_to_remember
                in things_to_remember_new["thing_to_remember"].tolist()
            ]

            # insert new items into table, ignoring existing ones 
            cursor.executemany("""
                insert into things_to_remember (entry_time, thing_to_remember)
                values (%s, %s)
                on conflict (thing_to_remember) do nothing;
            """, things_to_remember)
            cursor.execute("""
                insert into things_to_remember_history (entry_time, action, thing_to_remember)
                select entry_time
                    ,'Added'
                    ,thing_to_remember
                from things_to_remember
                on conflict (entry_time, action, thing_to_remember) do nothing;
            """)
            conn.commit()

            # pull any removed items  
            removed_things_to_remember = [
                thing_to_remember
                for thing_to_remember
                in things_to_remember_curr["thing_to_remember"].tolist()
                if thing_to_remember not in things_to_remember_new["thing_to_remember"].tolist()
            ]

            # delete all removed items 
            if removed_things_to_remember:
                placeholders = ", ".join("%s" for _ in removed_things_to_remember)
                cursor.execute(
                    f"delete from things_to_remember where thing_to_remember in ({placeholders})", removed_things_to_remember
                )
                conn.commit()

                # get removed list of things to remember and date
                things_to_remember_removed = [
                    (run_timestamp, "Removed", thing_to_remember)
                    for thing_to_remember
                    in removed_things_to_remember
                ]

                # insert removed items into table
                cursor.executemany("""
                    insert into things_to_remember_history (entry_time, action, thing_to_remember)
                    values (%s, %s, %s)     
                    on conflict (entry_time, action, thing_to_remember) do nothing;
                """, things_to_remember_removed)
                conn.commit()

            # rerun to pull updated data from database 
            st.session_state["things_to_remember_update"] = True
            st.rerun()

        # display success message
        if st.session_state["things_to_remember_update"]:
            st.success(f"[{run_timestamp}] Things to remember updated!")
            st.session_state["things_to_remember_update"] = False

            # level up things to remember fish
            cursor.execute("""
                update fish_config 
                set level = level + 1 
                where fish_mapping = %s
                ;
            """, ("Things to Remember",)) 
            conn.commit()

            cursor.execute("""
                update fish_config 
                set generation = generation + 1
                    ,level = 0
                where fish_mapping = %s
                    and level = 20
            """, ("Things to Remember",)) 
            conn.commit()

    cursor.close()


def render_dreams(run_timestamp, conn):
    """
    Render section: Dreams
    This section can be used to document dreams, like a dream journal.
    """

    # display header: log my dreams!
    st.header("Dreams")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        with st.form("dream_form", clear_on_submit = True, border = False):

            # offer various options for recording dreams:
            dream_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "dream"
            )

            # upload voice memo
            uploaded_file = st.file_uploader(
                "Upload a voice memo with dream recollection:",
                type=["m4a", "mp3", "wav", "mp4"]
            )
            # type text manually 
            dream_text = st.text_area("Enter text of dream recollection:")

            # if uploaded voice memo, save file name
            if uploaded_file:
                # display audio back to user 
                st.audio(uploaded_file)
                audio_bytes = uploaded_file.read()
                audio_file = uploaded_file.name
            else:
                audio_file = None

            # allow user to tag mood/people
            mood_tags = st.multiselect(
                "Enter mood tags:",
                ["Happy", "Funny", "Stressful", "Scary", "Sexy", "Romantic", "Adventurous", "Fantastical"],
                accept_new_options = True,
            )

            people_tags = st.multiselect(
                "Enter people tags:",
                ["Maddy", "Anthony", "Siena", "Evan", "Felice", "Anabel", "Dylan"],
                accept_new_options = True,
            )

            # Forms require a dedicated submit button
            dream_submit_button = st.form_submit_button("Submit Dream")

        # conditional logic if button is clicked
        if dream_submit_button:
            # save entry to database
            dream_data = (
                run_timestamp, 
                dream_date,
                dream_text,
                audio_file,
                mood_tags,
                people_tags
            )
            
            cursor.execute("""
                insert into dreams (entry_time, date, dream_text, file_name, mood_tags, people_tags)
                values (%s, %s, %s, %s, %s, %s);
            """, dream_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Dream data recorded!")

            # level up dream fish
            cursor.execute("""
                update fish_config 
                set level = level + 1 
                where fish_mapping = %s
                ;
            """, ("Dreams",)) 
            conn.commit()

            cursor.execute("""
                update fish_config 
                set generation = generation + 1
                    ,level = 0
                where fish_mapping = %s
                    and level = 20
            """, ("Dreams",)) 
            conn.commit()

    cursor.close()


def render_activity_roll(run_timestamp, conn):
    """
    Render section: Activity Roll
    This section can be used to randomly roll for an activity.
    """

    # display title: log my activities!
    st.header("Random Activity Roll")

    cursor = conn.cursor()

    # pull activity reroll option 
    cursor.execute("""
        select activity_rerolls_allowed 
        from configuration
    """)
    activity_rerolls_allowed = cursor.fetchone()[0]

    # pull list of activities config
    activity_config = pd.read_sql_query("""
        select * 
        from activity_config 
    """, conn)
    activity_menu = activity_config.to_dict("records")

    with st.expander("Click to expand/collapse", expanded = False):
        # specify activity requirements 
        time_of_day = st.radio(
            "Enter time of day:",
            ("Morning", "Afternoon", "Night"),
            index = None,
            horizontal = True
        )
        time_available = st.number_input(
            "Enter number of available minutes:",
            min_value = 0,
            step = 15,
            value = 0
        )
        participants_available = st.number_input(
            "Enter number of available participants (including yourself):",
            min_value = 1,
            value = 1
        )

        # grab last roll time from database
        cursor.execute("""
            select roll_time 
                ,activity
            from random_activity_rolls
            order by roll_time desc
            limit 1 
        """)
        last_roll = cursor.fetchone()

        # if there is not existing data, set last roll info to none 
        if not last_roll:
            last_roll_date = None
            last_roll_activity = None 
        else:
            last_roll_date = last_roll[0]
            last_roll_activity = last_roll[1]

        # compare last roll date to current date 
        current_date = datetime.strptime(run_timestamp, "%Y-%m-%d %I:%M:%S %p")
        roll_disabled = False
        if last_roll_date:
            # if last roll was today, disable roll button 
            if not activity_rerolls_allowed and last_roll_date.date() == current_date.date():
                roll_disabled = True

        # display button to push to database
        activities_roll_button = st.button(
            "Roll for Activity",
            disabled = roll_disabled
        )

        # conditional logic if button is clicked
        if activities_roll_button:
            # verify that all requirements are filled out 
            if time_of_day is None \
                or time_available is None \
                or participants_available is None:
                st.warning("Please specify all fields to roll an activity.")
                return

            # using activity requirements, get list of potential activities
            activity_options = [
                activity_dict["activity"]
                for activity_dict
                in activity_menu
                if time_of_day in activity_dict["accepted_times"]
                    and time_available >= activity_dict["time_requirement"]
                    and participants_available >= activity_dict["participant_requirement"]
            ]

            # if there are no activities that meet parameters, display warning 
            if not activity_options:
                st.warning("No activities meet the specifications.")
                return
            
            # randomly roll on an activity 
            new_activity_roll = random.choice(activity_options)

            # push random roll to database 
            random_roll_data = (
                current_date,
                new_activity_roll,
                time_of_day,
                time_available,
                participants_available
            )

            cursor.execute("""
                insert into random_activity_rolls (roll_time, activity, time_of_day, time_available, participants_available)
                values (%s, %s, %s, %s, %s)
            """, random_roll_data)
            conn.commit()

            # rerun to disable roll button
            st.rerun()

        # if there is a last activity of the day, display it with date
        if last_roll_date:
            _write_text(last_roll_activity)
            st.success(f"[{last_roll_date.strftime("%Y-%m-%d %I:%M:%S %p")}] Random activity rolled!")

    cursor.close()

def render_activities(run_timestamp, conn):
    """
    Render section: Activities
    This section can be used to document activities through the day.
    """

    # display title: log my activities!
    st.header("Activities")

    cursor = conn.cursor()

    # pull current activity list from database 
    activity_config = pd.read_sql_query("""
        select * 
        from activity_config 
    """, conn)
    activity_list = activity_config["activity"].tolist()

    # initialize activity menu with dictionary under each activity
    activity_menu = {
        activity_text: {
            "selected": False
        }
        for activity_text 
        in activity_list
    }

    with st.expander("Click to expand/collapse", expanded = False):
        activity_date = st.date_input(
            "Specify date:", 
            value = datetime.now(pytz.timezone(st.context.timezone)), 
            key = "activity")

        # loop through all activities to display
        _write_text("Select completed activities:")
        for activity_text in activity_menu:
            activity_dict = activity_menu[activity_text]

            # display activity with checkbox and save selection state
            activity_dict["selected"] = st.checkbox(activity_text)

        # loop through activities again if any were selected
        f_selected_activities = any(
            activity_menu[activity_text]["selected"] for activity_text in activity_menu 
        )
        if f_selected_activities:
            # rate resistance to each selected activity 
            _write_text("Rate intial resistance to activities:")
                
            for activity_text in activity_menu:
                activity_dict = activity_menu[activity_text]
                if activity_dict["selected"]:
                    activity_dict["resistance"] = st.slider(
                        f"{'&nbsp;' * 8}{activity_text}", 
                        min_value = 1,
                        max_value = 10, 
                        value = 10,
                        key = f"{activity_text} resistance"
                    )
            
            # rate enjoyment of each selected activity 
            _write_text("Rate active enjoyment of activities:")
                
            for activity_text in activity_menu:
                activity_dict = activity_menu[activity_text]
                # If activity is selected, display feedback 
                if activity_dict["selected"]:
                    activity_dict["enjoyment"] = st.slider(
                        f"{'&nbsp;' * 8}{activity_text}", 
                        min_value = 1,
                        max_value = 10, 
                        value = 10,
                        key = f"{activity_text} enjoyment"
                    )
        
            # rate retrospective enjoyment of each selected activity 
            _write_text("Rate retrospective enjoyment of activities:")
                
            for activity_text in activity_menu:
                activity_dict = activity_menu[activity_text]
                # If activity is selected, display feedback 
                if activity_dict["selected"]:
                    activity_dict["retrospective"] = st.slider(
                        f"{'&nbsp;' * 8}{activity_text}", 
                        min_value = 1,
                        max_value = 10, 
                        value = 10,
                        key = f"{activity_text} retrospective"
                    )
            
        # display button to push to database
        activities_submit_button = st.button("Submit Activities")

        # conditional logic if button is clicked
        if activities_submit_button and f_selected_activities:
            # save activities to database
            activity_data = [
                (
                    run_timestamp,
                    activity_date,
                    activity_text,
                    activity_menu[activity_text]["resistance"],
                    activity_menu[activity_text]["enjoyment"],
                    activity_menu[activity_text]["retrospective"],
                )
                for activity_text 
                in activity_menu
                if activity_menu[activity_text]["selected"]
            ]
            
            cursor.executemany("""
                insert into activities (entry_time, date, activity, resistance_rating, enjoyment_rating, retrospective_rating)
                values (%s, %s, %s, %s, %s, %s)
            """, activity_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Activity data recorded!")
            
            # level up activites fish
            cursor.execute("""
                update fish_config 
                set level = level + 1 
                where fish_mapping = %s
                ;
            """, ("Activities",)) 
            conn.commit()

            cursor.execute("""
                update fish_config 
                set generation = generation + 1
                    ,level = 0
                where fish_mapping = %s
                    and level = 20
            """, ("Activities",)) 
            conn.commit()
        elif activities_submit_button and not f_selected_activities:
            st.warning("Please select an activity.")

    cursor.close()


def render_journal(run_timestamp, conn):
    """
    Render section: Journal
    This section can be used to document journal entries, like a diary.
    """

    # display title: log my journal!
    st.header("Journal")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        with st.form("journal_form", clear_on_submit = True, border = False):
            journal_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "journal"
            )

            # upload voice memo
            uploaded_file = st.file_uploader(
                "Upload a voice memo with journal entry:",
                type=["m4a", "mp3", "wav", "mp4"]
            )
            # type text manually 
            journal_text = st.text_area("Enter text of journal entry:")

            # if uploaded voice memo, save file name
            if uploaded_file:
                # display audio back to user 
                st.audio(uploaded_file)
                audio_bytes = uploaded_file.read()
                audio_file = uploaded_file.name 
            else:
                audio_file = None

            # Forms require a dedicated submit button
            journal_submit_button = st.form_submit_button("Submit Journal")

        # conditional logic if button is clicked
        if journal_submit_button:
            # save entry to database
            journal_data = (
                run_timestamp, 
                journal_date,
                journal_text,
                audio_file
            )
            
            cursor.execute("""
                insert into journal (entry_time, date, journal_text, file_name)
                values (%s, %s, %s, %s)
            """, journal_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Journal data recorded!")

            # level up journal fish
            cursor.execute("""
                update fish_config 
                set level = level + 1 
                where fish_mapping = %s
                ;
            """, ("Journal",)) 
            conn.commit()

            cursor.execute("""
                update fish_config 
                set generation = generation + 1
                    ,level = 0
                where fish_mapping = %s
                    and level = 20
            """, ("Journal",)) 
            conn.commit()

    cursor.close()


def render_mood(run_timestamp, conn):
    """
    Render section: Mood
    This section can be used to document mood day-to-day.
    """

    # display title: log my mood!
    st.header("Mood")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        with st.form("mood_form", clear_on_submit = True, border = False):

            mood_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "mood"
            )

            # log how my day was
            general_day = st.radio(
                "How was your day?",
                ("Great :smiley:", "Good :blush:", "Okay :neutral_face:", "Bad :slightly_frowning_face:", "Terrible :sob:"),
                index = None,
                horizontal = True
            )

            # log descriptors for day
            _write_text("What was it like?")
            adventurous_day = st.checkbox("Adventurous :airplane:")
            sociable_day = st.checkbox("Socialable :handshake:")
            sad_day = st.checkbox("Sad :cry:")
            stressful_day = st.checkbox("Stressful :confounded:")
            angry_day = st.checkbox("Angry :rage:")
            restless_day = st.checkbox("Restless :firecracker:")
            productive_day = st.checkbox("Productive :chart_with_upwards_trend:")
            unremarkable_day = st.checkbox("Unremarkable :woman_shrugging:")

            day_descriptors_dict = {
                "Adventurous :airplane:": adventurous_day,
                "Socialable :handshake:": sociable_day,
                "Sad :cry:": sad_day,
                "Stressful :confounded:": stressful_day,
                "Angry :rage:": angry_day,
                "Restless :firecracker:": restless_day,
                "Productive :chart_with_upwards_trend:": productive_day,
                "Unremarkable :woman_shrugging:": unremarkable_day,
            }

            day_descriptors_list = [desc for desc, checkbox in day_descriptors_dict.items() if checkbox]

            # log how work was
            workday = st.radio(
                "How was work?",
                ("Great :smiley:", "Good :blush:", "Okay :neutral_face:", "Bad :slightly_frowning_face:", "Terrible :sob:", "N/A"),
                index = None,
                horizontal = True
            )

            # Forms require a dedicated submit button
            mood_submit_button = st.form_submit_button("Submit Mood")

        # conditional logic if button is clicked
        if mood_submit_button:
            # save entry to database
            mood_data = (
                run_timestamp, 
                mood_date,
                general_day,
                day_descriptors_list,
                workday
            )
            
            cursor.execute("""
                insert into mood (entry_time, date, how_was_your_day, day_descriptors, how_was_work)
                values (%s, %s, %s, %s, %s)
            """, mood_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Mood data recorded!")
            
            # level up mood fish
            cursor.execute("""
                update fish_config 
                set level = level + 1 
                where fish_mapping = %s
                ;
            """, ("Mood",)) 
            conn.commit()

            cursor.execute("""
                update fish_config 
                set generation = generation + 1
                    ,level = 0
                where fish_mapping = %s
                    and level = 20
            """, ("Mood",)) 
            conn.commit()

    cursor.close()


def configure_user_options(run_timestamp, conn):
    """
    Render section: Configure User Options.
    This section provides a table with user configuration.
    """
    
    # display header: log my things to remember!
    st.header("Configuration")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        if "configuration_update" not in st.session_state:
            st.session_state["configuration_update"] = False

        with st.form(key="configuration_form", border=False):
            # pull current reroll setting from database
            cursor.execute("""
                select activity_rerolls_allowed 
                from configuration
            """)
            activity_rerolls_allowed = cursor.fetchone()[0]

            # display toggle with default option 
            new_activity_rerolls_allowed = st.toggle(
                "Allow activity rerolls", 
                value = activity_rerolls_allowed
            )
            
            # pull current activity list from database 
            curr_activity_config = pd.read_sql_query("""
                select * 
                from activity_config 
            """, conn)

            # display with st.data_editor, which allows us to remove or edit items dynamically
            new_activity_config = st.data_editor(
                curr_activity_config,
                num_rows = "dynamic",
                column_config = {
                    "activity": st.column_config.TextColumn(
                        "Activity",
                        required = True,
                    ),
                    "accepted_times": st.column_config.MultiselectColumn(
                        "Accepted Times",
                        options = ["Morning", "Afternoon", "Night"],
                        required = True,
                        default = ["Morning", "Afternoon", "Night"],
                    ),
                    "time_requirement": st.column_config.NumberColumn(
                        "Time Requirement (Minutes)",
                        required = True,
                    ),
                    "participant_requirement": st.column_config.NumberColumn(
                        "Participant Requirement (Including Self)",
                        required = True,
                    )
                }
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Save Changes")

        if submit_button:
            # if reroll config was changed, update database table
            if new_activity_rerolls_allowed != activity_rerolls_allowed:
                cursor.execute(f"""
                    update configuration
                    set activity_rerolls_allowed = {new_activity_rerolls_allowed};
                """)

            # remove existing config 
            cursor.execute("""
                truncate table activity_config
            """)
            conn.commit()
            
            # update activity config table
            new_activity_config_records = [tuple(vals) for vals in new_activity_config.to_numpy()]
            cursor.executemany("""
                insert into activity_config (activity, accepted_times, time_requirement, participant_requirement)
                values (%s, %s, %s, %s)
            """, new_activity_config_records)
            conn.commit()

            # rerun to pull updated data from database 
            st.session_state["configuration_update"] = True
            st.rerun()

        # display success message
        if st.session_state["configuration_update"]:
            st.success(f"[{run_timestamp}] Configuration updated!")
            st.session_state["configuration_update"] = False

    cursor.close()


def _write_text(
    text: str,
    size: str = "14"
):
    """
    Display text with custom font size to match Streamlit labels.
    """
    return st.markdown(f"<span style='font-size: {size}px;'>{text}</span>", unsafe_allow_html = True)


if __name__ == "__main__":
    main()