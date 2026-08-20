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
    render_to_do(run_timestamp, conn)
    render_dreams(run_timestamp, conn)
    render_activities(run_timestamp, conn)
    render_journal(run_timestamp, conn)
    render_reflections(run_timestamp, conn)
    render_bingo(run_timestamp, conn)
    render_activity_roll(run_timestamp, conn)
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

    with st.expander("Click to expand/collapse", expanded=False):
        # display table with fish attributes
        fish_df = pd.DataFrame(fish_config_w_daddys.values())
        fish_df = fish_df.sort_values(["fish_id"], ignore_index = True)
        fish_df = fish_df[["fish_name", "fish_mapping", "fish_age", "generation", "level"]]
        fish_df = fish_df.rename(columns={
            "fish_name": "Name",
            "fish_mapping": "Mapping",
            "fish_age": "Age",
            "generation": "Gen",
            "level": "Level"
        })
        st.table(fish_df)

        if st.button("Refresh Aquarium"):
            st.rerun()

    cursor.close()

def render_to_do(run_timestamp, conn):
    """
    Render section: To-Do.
    This section keeps a running, editable list of to-do.
    """
    
    # display header: log my to-do!
    st.header("To-Do")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        if "to_do_update" not in st.session_state:
            st.session_state["to_do_update"] = False

        with st.form(key = "to_do_form", border=False):
            # read to-do from sql
            to_do_curr = pd.read_sql_query("""
                select to_do_item 
                from to_do 
                order by entry_time
            """, conn)

            # display with st.data_editor, which allows us to remove or edit items dynamically
            to_do_new = st.data_editor(
                to_do_curr,
                num_rows = "dynamic",
                column_config = {
                    "to_do_item": st.column_config.TextColumn(
                        "To-Do Item",
                        width = 275
                    )
                }
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Save Changes")

        if submit_button:
            # get updated list of to-do and date
            to_do = [
                (run_timestamp, to_do_item)
                for to_do_item
                in to_do_new["to_do_item"].tolist()
            ]

            # insert new items into table, ignoring existing ones 
            cursor.executemany("""
                insert into to_do (entry_time, to_do_item)
                values (%s, %s)
                on conflict (to_do_item) do nothing;
            """, to_do)
            cursor.execute("""
                insert into to_do_history (entry_time, action, to_do_item)
                select entry_time
                    ,'Added'
                    ,to_do_item
                from to_do
                on conflict (entry_time, action, to_do_item) do nothing;
            """)
            conn.commit()

            # pull any removed items  
            removed_to_do = [
                to_do_item
                for to_do_item
                in to_do_curr["to_do_item"].tolist()
                if to_do_item not in to_do_new["to_do_item"].tolist()
            ]

            # delete all removed items 
            if removed_to_do:
                placeholders = ", ".join("%s" for _ in removed_to_do)
                cursor.execute(
                    f"delete from to_do where to_do_item in ({placeholders})", removed_to_do
                )
                conn.commit()

                # get removed list of to-do and date
                to_do_removed = [
                    (run_timestamp, "Removed", to_do_item)
                    for to_do_item
                    in removed_to_do
                ]

                # insert removed items into table
                cursor.executemany("""
                    insert into to_do_history (entry_time, action, to_do_item)
                    values (%s, %s, %s)     
                    on conflict (entry_time, action, to_do_item) do nothing;
                """, to_do_removed)
                conn.commit()

            # rerun to pull updated data from database 
            st.session_state["to_do_update"] = True
            st.rerun()

        # display success message
        if st.session_state["to_do_update"]:
            st.success(f"[{run_timestamp}] To-Do updated!")
            st.session_state["to_do_update"] = False

            # level up relevant fish 
            current_date = datetime.strptime(run_timestamp, "%Y-%m-%d %I:%M:%S %p")
            _level_up_fish("To-Do", current_date.date(), conn)

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
            
            # allow user to tag mood/people, with existing values as suggestions
            # first, mood 
            existing_mood_tags = pd.read_sql_query("""
                select distinct long.mood_tag
                from dreams d
                cross join lateral 
                    unnest(d.mood_tags) as long(mood_tag)
                ;
            """, conn)
            mood_tags = st.multiselect(
                "Enter mood tags:",
                existing_mood_tags,
                accept_new_options = True,
            )

            # then people tags 
            existing_people_tags = pd.read_sql_query("""
                select distinct long.people_tag
                from dreams d
                cross join lateral 
                    unnest(d.people_tags) as long(people_tag)
                ;
            """, conn)
            people_tags = st.multiselect(
                "Enter people tags:",
                existing_people_tags,
                accept_new_options = True,
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

            # level up relevant fish 
            _level_up_fish("Dreams", dream_date, conn)

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
    existing_activities = pd.read_sql_query("""
        select distinct activity
        from activities 
    """, conn)

    with st.expander("Click to expand/collapse", expanded = False):
        activity_date = st.date_input(
            "Specify date:", 
            value = datetime.now(pytz.timezone(st.context.timezone)), 
            key = "activity")

        # multiselect activities
        selected_activities = st.multiselect(
            "Select completed activities:",
            existing_activities,
            accept_new_options = True
        )

        # if any are selected
        if selected_activities:
            # initialize activity menu with dictionary 
            activity_menu = {
                activity_text: {}
                for activity_text 
                in selected_activities
            }

            # rate resistance to each selected activity 
            _write_text("Rate intial resistance to activities:")
                
            for activity_text in selected_activities:
                activity_menu[activity_text]["resistance"] = st.slider(
                    f"{'&nbsp;' * 8}{activity_text}", 
                    min_value = 1,
                    max_value = 10, 
                    value = 10,
                    key = f"{activity_text} resistance"
                )
            
            # rate enjoyment of each selected activity 
            _write_text("Rate active enjoyment of activities:")
                
            for activity_text in selected_activities:
                activity_menu[activity_text]["enjoyment"] = st.slider(
                    f"{'&nbsp;' * 8}{activity_text}", 
                    min_value = 1,
                    max_value = 10, 
                    value = 10,
                    key = f"{activity_text} enjoyment"
                )
        
            # rate retrospective enjoyment of each selected activity 
            _write_text("Rate retrospective enjoyment of activities:")
                
            for activity_text in selected_activities:
                activity_menu[activity_text]["retrospective"] = st.slider(
                    f"{'&nbsp;' * 8}{activity_text}", 
                    min_value = 1,
                    max_value = 10, 
                    value = 10,
                    key = f"{activity_text} retrospective"
                )
            
        # display button to push to database
        activities_submit_button = st.button("Submit Activities")

        # conditional logic if button is clicked
        if activities_submit_button and selected_activities:
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
                in selected_activities
            ]
            
            cursor.executemany("""
                insert into activities (entry_time, date, activity, resistance_rating, enjoyment_rating, retrospective_rating)
                values (%s, %s, %s, %s, %s, %s)
            """, activity_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Activity data recorded!")
            
            # level up relevant fish 
            _level_up_fish("Activities", activity_date, conn)
        elif activities_submit_button and not selected_activities:
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

            # log how my day was
            overall_day_rating = st.radio(
                "How was your day?",
                ("Great :smiley:", "Good :blush:", "Okay :neutral_face:", "Bad :slightly_frowning_face:", "Terrible :sob:"),
                index = None,
                horizontal = True
            )

            # log how work was
            work_rating = st.radio(
                "How was work?",
                ("Great :smiley:", "Good :blush:", "Okay :neutral_face:", "Bad :slightly_frowning_face:", "Terrible :sob:", "N/A"),
                index = None,
                horizontal = True
            )
            
            # allow user to tag mood/people, with existing values as suggestions
            # first, mood 
            existing_mood_tags = pd.read_sql_query("""
                select distinct long.mood_tag
                from journal j
                cross join lateral 
                    unnest(j.mood_tags) as long(mood_tag)
                ;
            """, conn)
            mood_tags = st.multiselect(
                "Enter mood tags:",
                existing_mood_tags,
                accept_new_options = True,
            )

            # then people tags 
            existing_people_tags = pd.read_sql_query("""
                select distinct long.people_tag
                from journal j
                cross join lateral 
                    unnest(j.people_tags) as long(people_tag)
                ;
            """, conn)
            people_tags = st.multiselect(
                "Enter people tags:",
                existing_people_tags,
                accept_new_options = True,
            )

            # upload journal voice memo
            uploaded_file = st.file_uploader(
                "Upload a voice memo with journal entry:",
                type=["m4a", "mp3", "wav", "mp4"]
            )
            # type journal text manually 
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
                overall_day_rating,
                mood_tags,
                people_tags,
                work_rating,
                journal_text,
                audio_file
            )
            
            cursor.execute("""
                insert into journal (entry_time, date, overall_day_rating, mood_tags, people_tags, work_rating, journal_text, file_name)
                values (%s, %s, %s, %s, %s, %s, %s, %s)
            """, journal_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Journal data recorded!")

            # level up relevant fish 
            _level_up_fish("Journal", journal_date, conn)

    cursor.close()


def render_reflections(run_timestamp, conn):
    """
    Render section: Reflections.
    This section keeps a running, editable list of reflections.
    """
    
    # display header: log my reflections!
    st.header("Reflections")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        if "reflections_update" not in st.session_state:
            st.session_state["reflections_update"] = False

        with st.form(key = "reflections_form", border=False):
            # read to-do from sql
            reflections_curr = pd.read_sql_query("""
                select reflection 
                from reflections 
                order by entry_time
            """, conn)

            # display with st.data_editor, which allows us to remove or edit items dynamically
            reflections_new = st.data_editor(
                reflections_curr,
                num_rows = "dynamic",
                column_config = {
                    "reflection": st.column_config.TextColumn(
                        "Reflection",
                        width = 275
                    )
                }
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Save Changes")

        if submit_button:
            # get updated list of to-do and date
            reflections = [
                (run_timestamp, reflection)
                for reflection
                in reflections_new["reflection"].tolist()
            ]

            # insert new items into table, ignoring existing ones 
            cursor.executemany("""
                insert into reflections (entry_time, reflection)
                values (%s, %s)
                on conflict (reflection) do nothing;
            """, reflections)
            conn.commit()

            # pull any removed items  
            removed_reflections = [
                reflection
                for reflection
                in reflections_curr["reflection"].tolist()
                if reflection not in reflections_new["reflection"].tolist()
            ]

            # delete all removed items 
            if removed_reflections:
                placeholders = ", ".join("%s" for _ in removed_reflections)
                cursor.execute(
                    f"delete from reflections where reflection in ({placeholders})", removed_reflections
                )
                conn.commit()

            # rerun to pull updated data from database 
            st.session_state["reflections_update"] = True
            st.rerun()

        # display success message
        if st.session_state["reflections_update"]:
            st.success(f"[{run_timestamp}] Reflections updated!")
            st.session_state["reflections_update"] = False

            # level up relevant fish 
            current_date = datetime.strptime(run_timestamp, "%Y-%m-%d %I:%M:%S %p")
            _level_up_fish("Reflections", current_date.date(), conn)

    cursor.close()



def render_bingo(run_timestamp, conn):
    """
    Render section: Bingo
    This section can be used to document yearly bingo square progress.
    """

    st.header("Bingo")

    cursor = conn.cursor()

    bingo_dim = 5

    with st.expander("Click to expand/collapse", expanded=False):

        # read bingo square from database 
        bingo_square_pd = pd.read_sql_query("""
            select * 
            from bingo_square 
        """, conn)
        bingo_square = bingo_square_pd.to_dict("records")

        # create matrix (list of lists) of bingo 
        bingo_matrix = {
            row + 1: {}
            for row 
            in range(bingo_dim) 
        }

        for square in bingo_square:
            bingo_matrix[square["row"]][square["column"]] = square

        if "selected_bingo_square" not in st.session_state:
            st.session_state.selected_bingo_square = None

        # display bingo board
        with st.container(key="bingo_board"):
            # build square rules
            completed_square_rules = []

            # if square is completed, fill in background color
            for square in bingo_square:
                if square["progress"] >= square["target"]:
                    completed_square_rules.append(
                        f"""
                        .st-key-bingo_square_{square["id"]}
                        div[data-testid="stButton"] > button {{
                            background-color: #d9ead3 !important;
                        }}
                        """
                    )

            # for all squares, define formatting such that squares are touching
            st.markdown(
                f"""
                <style>

                .st-key-bingo_board
                div[data-testid="stButton"] > button {{
                    width: 100%;
                    height: 100px;
                    padding: 0.25rem;
                    white-space: normal;
                    margin-top: -10px;
                    margin-bottom: -10px;
                    border-radius: 0px !important;
                }}

                .st-key-bingo_board
                div[data-testid="stHorizontalBlock"] {{
                    gap: 0rem;
                }}

                {''.join(completed_square_rules)}

                </style>
                """,
                unsafe_allow_html=True,
            )

            # render the bingo board
            for row in range(1, 1 + bingo_dim):
                # define square grid 
                cols = st.columns(bingo_dim, gap="small")

                for col in range(1, 1 + bingo_dim):
                    square = bingo_matrix[row][col]

                    with cols[col - 1]:

                        # Give each individual square its own CSS scope
                        # so the completed-square background can target
                        # exactly this square.
                        with st.container(
                            key=f"bingo_square_{square['id']}"
                        ):

                            label = (
                                f"{square['title']}\n\n"
                                f"{square['progress']} / {square['target']}"
                            )

                            if square["progress"] >= square["target"]:
                                disable_button = True 
                            else:
                                disable_button = False

                            if st.button(
                                label,
                                key=f"bingo_{square['id']}",
                                use_container_width=True,
                                disabled = disable_button
                            ):
                                st.session_state.selected_bingo_square = (
                                    square["id"]
                                )

        # find selected bingo square
        selected_id = st.session_state.selected_bingo_square
        selected_square = None

        if selected_id is not None:

            for row in bingo_matrix.values():
                for square in row.values():
                    if square["id"] == selected_id:
                        selected_square = square
                        break

                if selected_square is not None:
                    break

        # edit selected square
        if selected_square is not None:

            st.subheader(selected_square["title"])

            bingo_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "bingo"
            )

            progress = st.number_input(
                "Enter progress:",
                min_value=0,
                max_value=selected_square["target"],
                value=selected_square["progress"],
                key=f"progress_{selected_id}",
            )

            notes = st.text_area(
                "Enter additional details:",
                key=f"notes_{selected_id}",
            )

            # display submit button
            if st.button(
                "Submit Bingo Progress",
                key="submit_bingo",
            ):

                # update progress counter
                cursor.execute("""
                    update bingo_square 
                    set progress = %s
                    where id = %s
                    ;
                """, (progress, selected_id)) 
                conn.commit()

                # add notes
                bingo_data = (
                    run_timestamp, 
                    bingo_date,
                    selected_id,
                    selected_square["title"],
                    notes
                )
                
                cursor.execute("""
                    insert into bingo_notes (entry_time, date, id, title, notes)
                    values (%s, %s, %s, %s, %s)
                """, bingo_data)
                conn.commit()
                    
                # level up relevant fish
                _level_up_fish("Bingo", bingo_date, conn, allow_multiple_level_ups_per_day = True)

                st.session_state.bingo_success = (
                    f"[{run_timestamp}] Bingo Progress Recorded!"
                )

                st.rerun()

        # display success message 
        if "bingo_success" in st.session_state:
            st.success(st.session_state.bingo_success)
            del st.session_state.bingo_success

    cursor.close()


def configure_user_options(run_timestamp, conn):
    """
    Render section: Configure User Options.
    This section provides a table with user configuration.
    """
    
    # display header: log my to-do!
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


def _level_up_fish(
    mapping: str, 
    date: datetime,
    conn,
    allow_multiple_level_ups_per_day: bool = False
):
    """
    Level up the fish corresponding to the given mapping.
    """

    cursor = conn.cursor()

    # level up fish with the given mapping
    if allow_multiple_level_ups_per_day:
        cursor.execute("""
            update fish_config 
            set level = level + 1 
                ,last_updated_date = %s
            where fish_mapping = %s
            ;
        """, (date, mapping)) 
    else:
        cursor.execute("""
            update fish_config 
            set level = level + 1 
                ,last_updated_date = %s
            where fish_mapping = %s
                and last_updated_date <> %s
            ;
        """, (date, mapping, date)) 

    conn.commit()

    # if the fish just hit level 20, reset back to level 0 
    # but update generation 
    cursor.execute("""
        update fish_config 
        set generation = generation + 1
            ,level = 0
        where fish_mapping = %s
            and level = 20
    """, (mapping,)) 
    conn.commit()

    cursor.close()
    

if __name__ == "__main__":
    main()