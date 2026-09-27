from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import re
import html

import streamlit as st
import streamlit.components.v1 as components

import psycopg
import pytz
import random

from utilities.utilities import _write_text
from components.aquarium import aquarium_component
from components.bingo import bingo_component

def log():
    """
    Log my life!
    """

    # record run time in relevant timezone
    user_timezone = pytz.timezone(st.context.timezone)
    run_timestamp = datetime.now(user_timezone).strftime("%Y-%m-%d %I:%M:%S %p")

    # initialize database connection
    conn = psycopg.connect(
        st.secrets["database"]["url"], 
        options = "-c search_path=public"
    )

    # render sections
    st.title("Life Log")
    render_aquarium(conn)
    render_to_do(run_timestamp, conn)
    render_habits(run_timestamp, conn)
    render_activities(run_timestamp, conn)
    render_journal(run_timestamp, conn)
    render_dreams(run_timestamp, conn)
    render_bingo(run_timestamp, conn)
    render_reflections(run_timestamp, conn)
    render_lifestyle(run_timestamp, conn)
    render_health(run_timestamp, conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


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
    fish_config_pd["fish_id"] = fish_config_pd["fish_id"].astype(str)
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
            daddy_dict["generation"] = fish_dict_copy["generation"] - 1
            daddy_dict["level"] = 19

            # update baby fish positioning based on daddy
            fish_dict_copy["top1"] = fish_dict_copy["top1"] + 5
            fish_dict_copy["top2"] = fish_dict_copy["top2"] + 5
            fish_dict_copy["delay"] = fish_dict_copy["delay"] + 0.7
            fish_dict_copy["speed"] = fish_dict_copy["speed"]

            fish_config_w_daddys[daddy_dict["fish_id"]] = daddy_dict

        # add dictionary to final fish config list
        fish_config_w_daddys[fish_dict_copy["fish_id"]] = fish_dict_copy

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
        # generations 1 and on get a light body 
        if fish_dict["generation"] == 0:
            fish_svg_text = re.sub(
                r'<path\b(?=[^>]*\bid="body-light")[^>]*/>',
                '',
                fish_svg_text
            )

        # remove tail lines when relevant depending on generation
        # generation 2 get two tail lines, 3 gets 4, and onwards gets all 6
        if fish_dict["generation"] <= 1:
            tail_lines_to_remove = range(1, 7)
        elif fish_dict["generation"] == 2:
            tail_lines_to_remove = range(3, 7)
        elif fish_dict["generation"] == 3:
            tail_lines_to_remove = range(5, 7)
        else:
            tail_lines_to_remove = []

        for i in tail_lines_to_remove:
            fish_svg_text = re.sub(
                rf'<path\b(?=[^>]*\bid="tail-line-{i}")[^>]*/>',
                '',
                fish_svg_text
            )

        # remove scales when relevant depending on generation 
        # generation 5 gets scale 01
        # generation 6 gets scales 01–02
        # etc.
        max_scale = max(0, fish_dict["generation"] - 4)
        removed_scales = range(max_scale + 1, 150)
        removed_scale_numbers = "|".join(
            f"{i}" for i in removed_scales
        )

        # remove individual scale paths generations 0/1/2
        fish_svg_text = re.sub(
            rf'<path\b(?=[^>]*\bid="scale-(?:[^"]+)")[^>]*/>',
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

    # define dynamic html content 
    content = f"""
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

        <!-- insert fish -->
        {
            " ".join([fish_dict["svg"] for fish_dict in fish_config_w_daddys.values()])
        }

    </div>
    """

    # display aquarium
    aquarium_component(
        data = {"html": content},
        key = "aquarium_component"
    )

    with st.expander("Click to expand/collapse", expanded=False):
        # display table with fish attributes
        fish_df = pd.DataFrame(fish_config_w_daddys.values())
        fish_df = fish_df[~fish_df["fish_id"].str.startswith("dad")]
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
            # update random seed
            st.session_state.aquarium_seed = random.randint(0, 999999)
            st.rerun()

    cursor.close()


def render_habits(run_timestamp, conn):
    """
    Render section: Habits.
    This section keeps a running, editable list of recurring habits.
    """

    st.header("Habits")

    cursor = conn.cursor()

    current_date = datetime.strptime(
        run_timestamp,
        "%Y-%m-%d %I:%M:%S %p"
    ).date()

    frequency_options = [
        "Daily",
        "Weekly",
        "Monthly"
    ]

    with st.expander(
        "Click to expand/collapse",
        key="habits_expander"
    ):

        # keep track of whether habits was just updated
        if "habits_update" not in st.session_state:
            st.session_state["habits_update"] = False

        # pull habits from database
        if "habits_og_data" not in st.session_state:
            st.session_state["habits_og_data"] = pd.read_sql_query("""
                with merged_habits as (
                    select hbt.id
                        ,hbt.habit
                        ,hbt.target
                        ,hbt.frequency
                        ,prgrs.date
                        ,prgrs.progress
                    from habits as hbt
                    left join habits_progress as prgrs
                        on hbt.id = prgrs.habit_id
                )
                select id
                    ,habit
                    ,target
                    ,coalesce(sum(
                        case 
                            when frequency = 'Daily' 
                                and date = current_date 
                            then progress
                            when frequency = 'Weekly' 
                                and date >= date_trunc('week', current_date) 
                                and date < date_trunc('week', current_date) + interval '1 week' 
                            then progress
                            when frequency = 'Monthly' 
                                and date_trunc('month', date) = date_trunc('month', current_date)
                            then progress  
                        end
                    ), 0) as current
                    ,frequency
                from merged_habits
                group by id
                    ,habit
                    ,target
                    ,frequency
                order by id
            """, conn)

            # create copy of data which will get displayed and updated 
            st.session_state["habits_data"] = (
                st.session_state["habits_og_data"].copy()
            )

        # display habtis table 
        habits_data = st.session_state["habits_data"]

        if len(habits_data) == 0:
            st.warning("Add habits using the Configure Habits drop-down.")
        else:
            habits_display = habits_data.copy()

            # define progress of current completions out of target 
            habits_display["progress"] = (
                habits_display["current"].astype(int).astype(str)
                + " / "
                + habits_display["target"].astype(int).astype(str)
            )

            # for incomplete habits, display a checkmark completion button
            habits_display["complete"] = np.where(
                habits_display["current"] >= habits_display["target"],
                "",
                "✔"
            )

            # display read-only table of habits
            st.data_editor(
                habits_display[["habit", "progress", "complete"]],
                hide_index = True,
                disabled = ["habit", "progress"],
                column_config = {
                    "habit": st.column_config.TextColumn(
                        "Habit"
                    ),
                    "progress": st.column_config.TextColumn(
                        "Progress",
                        width = 15,
                        alignment = "center"
                    ),
                    "complete": st.column_config.ButtonColumn(
                        "Complete",
                        key = "complete",
                        help = "Increase progress by 1",
                        type = "primary",
                        width = 15,
                        alignment = "center"
                    )
                }
            )

        # handle completion buttons
        if st.session_state.get("complete"):
            row = st.session_state["complete"]["row"]
            # add one to current completions
            st.session_state["habits_data"].loc[
                row,
                "current"
            ] += 1

            st.rerun()

        # display habit configure options 
        with st.expander("Configure Habits", expanded = False, type = "compact"):
            option = st.selectbox("Select action:",
                options = [
                    "Add Habit",
                    "Edit Habit",
                    "Delete Habit"
                ],
                index = None,
                key = "configure_habits_option"
            )

            # add habits 
            if option == "Add Habit":

                # allow user to input habit details 
                new_habit = st.text_input(
                    "Enter habit text:"
                )

                new_frequency = st.selectbox(
                    "Enter intended habit frequency:",
                    frequency_options
                )

                if new_frequency == "Daily":
                    period = "day" 
                elif new_frequency == "Weekly":
                    period = "week"
                elif new_frequency == "Monthly":
                    period = "month"

                new_target = st.number_input(
                    f"Enter intended habit completions per {period}:",
                    min_value = 1,
                    value = 1,
                    step = 1
                )

                # button to save added habit 
                if st.button("Save Added Habit"):
                    if new_habit.strip() == "":
                        st.warning("Please enter habit text.")
                    elif new_habit in list(st.session_state["habits_data"]["habit"]):
                        st.warning("Habit already exists.")
                    else:
                        new_row = pd.DataFrame([{
                            "id": np.nan,
                            "habit": new_habit.strip(),
                            "target": int(new_target),
                            "current": 0,
                            "frequency": new_frequency
                        }])

                        st.session_state["habits_data"] = pd.concat(
                            [
                                st.session_state["habits_data"],
                                new_row
                            ],
                            ignore_index = True
                        )

                        st.rerun()

            # edit habits
            elif option == "Edit Habit":

                habits_data = st.session_state["habits_data"]
                habit_options = list(habits_data.index)

                # have user to select existing habit 
                selected_index = st.selectbox(
                    "Select habit to edit:",
                    options = habit_options,
                    format_func = lambda index: (
                        habits_data.loc[index, "habit"]
                    ),
                    index = None
                )

                # allow user to edit existing habit details 
                if selected_index is not None:
                    selected_row = habits_data.loc[selected_index]

                    edited_habit = st.text_input(
                        "Enter edited habit text:",
                        value = selected_row["habit"],
                    )

                    edited_frequency = st.selectbox(
                        "Enter edited habit frequency:",
                        options = frequency_options,
                        index = frequency_options.index(selected_row["frequency"]),
                    )

                    if edited_frequency == "Daily":
                        period = "day" 
                    elif edited_frequency == "Weekly":
                        period = "week"
                    elif edited_frequency == "Monthly":
                        period = "month"

                    edited_target = st.number_input(
                        f"Enter edited habit completions per {period}:",
                        min_value = 1,
                        value = selected_row["target"],
                        step = 1
                    )

                    if st.button("Save Edited Habit"):
                        if edited_habit.strip() == "":
                            st.warning("Please enter edited habit text.")
                        elif edited_habit != selected_row["habit"] and edited_habit in list(st.session_state["habits_data"]["habit"]):
                            st.warning("Habit already exists.")
                        else:
                            st.session_state["habits_data"].loc[
                                selected_index,
                                "habit"
                            ] = edited_habit.strip()

                            st.session_state["habits_data"].loc[
                                selected_index,
                                "target"
                            ] = int(edited_target)

                            st.session_state["habits_data"].loc[
                                selected_index,
                                "frequency"
                            ] = edited_frequency

                            st.rerun()

            # delete habits
            elif option == "Delete Habit":

                habits_data = st.session_state["habits_data"]
                habit_options = list(habits_data.index)

                # have user to select existing habit 
                selected_index = st.selectbox(
                    "Select habit to delete:",
                    options = habit_options,
                    format_func = lambda index: (
                        habits_data.loc[index, "habit"]
                    )
                )

                if st.button("Save Deleted Habit"):
                    st.session_state["habits_data"] = (
                        st.session_state["habits_data"]
                        .drop(index = selected_index)
                        .reset_index(drop = True)
                    )

                    st.rerun()

            st.divider()

        if st.button(
            "Save Changes",
            key="save_habits_button"
        ):
            habits_to_save = (
                st.session_state["habits_data"].copy()
            )

            original_habits = (
                st.session_state["habits_og_data"]
            )

            # delete removed habits
            original_ids = set(original_habits["id"].dropna())
            edited_ids = set(habits_to_save["id"].dropna())
            deleted_ids = original_ids - edited_ids

            for habit_id in deleted_ids:
                cursor.execute("""
                    delete habits
                    where id = %s
                """, (int(habit_id),))

            # insert new habits 
            new_habits = habits_to_save[habits_to_save["id"].isna()].copy()

            for index, row in new_habits.iterrows():
                cursor.execute("""
                    insert into habits (
                        habit,
                        target,
                        frequency
                    )
                    values (%s, %s, %s)
                    returning id
                """, (
                    row["habit"],
                    int(row["target"]),
                    row["frequency"]
                ))

                # update session data to contain generated id 
                new_id = cursor.fetchone()[0]
                habits_to_save.at[index, "id"] = new_id

            # update habits and save progress in database
            for _, row in habits_to_save.iterrows():
                # update habits in case text/target/frequency were updated 
                cursor.execute("""
                    update habits
                    set habit = %s,
                        target = %s,
                        frequency = %s
                    where id = %s
                """, (
                    row["habit"],
                    int(row["target"]),
                    row["frequency"],
                    int(row["id"])
                ))

                # update habits progress for the day
                cursor.execute("""
                    insert into habits_progress (
                        habit_id,
                        date,
                        progress
                    )
                    values (%s, %s, %s)
                    on conflict (habit_id, date)
                    do update set
                        progress = excluded.progress
                """, (
                    int(row["id"]),
                    current_date,
                    int(row["current"])
                ))

            conn.commit()

            # flag that habits were just updated 
            st.session_state["habits_update"] = True

            # delete habits data from session state
            del st.session_state["habits_og_data"]
            del st.session_state["habits_data"]

            st.rerun()

        # display success message 
        if st.session_state["habits_update"]:
            st.success(f"[{run_timestamp}] Habits updated!")
            st.session_state["habits_update"] = False

            # level up relevant fish 
            _level_up_fish("Habits", current_date, conn)

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

    with st.expander(
        "Click to expand/collapse",
        expanded=False
    ):

        # read bingo square from database
        bingo_square_pd = pd.read_sql_query(
            """
            select *
            from bingo_square
            """,
            conn
        )
        bingo_square = bingo_square_pd.to_dict("records")

        # in database, the bingo is long by each item with a row/col value
        # transform that data into a square matrix
        bingo_matrix = {
            row + 1: {}
            for row in range(bingo_dim)
        }

        for square in bingo_square:
            bingo_matrix[square["row"]][square["column"]] = square

        # we will store selected squares in session state
        if "selected_bingo_square" not in st.session_state:
            st.session_state.selected_bingo_square = None

        # build bingo board html
        board_html = '<div class="bingo-grid">'

        for row in range(1, bingo_dim + 1):
            for col in range(1, bingo_dim + 1):
                square = bingo_matrix[row][col]

                # escape database content
                square_id = html.escape(
                    str(square["id"]),
                    quote=True
                )

                title = html.escape(
                    str(square["title"])
                )

                progress = square["progress"]
                target = square["target"]

                # determine completed status
                completed = (progress >= target)

                # completed squares will be highlighted in green
                if completed:
                    background = "#d9ead3"
                    completed_class = " completed"
                else:
                    background = "#ffffff"
                    completed_class = ""

                # determine what to display for square progress
                # one-time goals will not get any progress tracker
                if target == 1:
                    progress_html = ""
                # if no progress, show original target
                elif progress == 0:
                    progress_html = f'<span class="bingo-progress">x{target}</span>'
                # if completed, show original target struck through
                elif progress >= target:
                    progress_html = f'<span class="bingo-progress"><s>x{target}</s></span>'
                # otherwise, strike through target and replace with remaining amount
                else:
                    remaining = target - progress
                    progress_html = f'<span class="bingo-progress"><s>x{target}</s> x{remaining}</span>'

                # build bingo board html
                board_html += f"""
                    <button 
                        class="bingo-square
                            {completed_class}" 
                        data-bingo-id="{square_id}" 
                        style="background-color:
                            {background};">

                    <span class="bingo-title">
                    {title}
                    </span>

                    {progress_html}

                    </button>
                """

        board_html += '</div>'

        # handle clicks on squares
        result = bingo_component(
            data = {"html": board_html},
            key = "bingo_board_component"
        )

        clicked_id = getattr(
            result,
            "bingo_clicked",
            None
        )

        if clicked_id is not None:
            # if the same square is clicked again, deselect it 
            if st.session_state.selected_bingo_square == clicked_id:
                st.session_state.selected_bingo_square = None
            else:
                st.session_state.selected_bingo_square = clicked_id

        # find selected square
        selected_id = st.session_state.selected_bingo_square
        selected_square = None

        if selected_id is not None:
            for row in bingo_matrix.values():
                for square in row.values():
                    if str(square["id"]) == str(selected_id):
                        selected_square = square
                        break

                if selected_square is not None:
                    break

        # show details to submit progress on selected square 
        if selected_square is not None:
            st.subheader(selected_square["title"])

            bingo_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "bingo"
            )   

            # allow freeform notes 
            notes = st.text_area(
                "Enter additional details:",
                key = f"notes_{selected_id}",
            )

            # button to submit progress
            if st.button(
                "Submit Bingo Progress",
                key = "submit_bingo",
            ):
                # increment progress by 1
                new_progress = selected_square["progress"] + 1

                cursor.execute(
                    """
                    update bingo_square
                    set progress = %s
                    where id = %s
                    ;
                    """,
                    (new_progress, selected_id)
                )

                conn.commit()

                # add notes for this progress
                bingo_data = (
                    run_timestamp,
                    bingo_date,
                    selected_id,
                    selected_square["title"],
                    notes
                )

                cursor.execute(
                    """
                    insert into bingo_notes
                    (
                        entry_time,
                        date,
                        id,
                        title,
                        notes
                    )
                    values (%s, %s, %s, %s, %s)
                    """,
                    bingo_data
                )

                conn.commit()

                # level up the relevant fish
                _level_up_fish(
                    "Bingo",
                    bingo_date,
                    conn,
                    allow_multiple_level_ups_per_day=True
                )

                # save success message
                st.session_state.bingo_success = f"[{run_timestamp}] Bingo Progress Recorded!"

                st.rerun()

        # display success message
        if "bingo_success" in st.session_state:
            st.success(st.session_state.bingo_success)
            del st.session_state.bingo_success

    cursor.close()


def render_lifestyle(run_timestamp, conn):
    """
    Render section: Lifestyle.
    This section keeps a running, editable list of lifestyle.
    """
    
    # display header: log my lifestyle!
    st.header("Lifestyle")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        if "lifestyle_update" not in st.session_state:
            st.session_state["lifestyle_update"] = False

        with st.form(key = "lifestyle_form", border=False):
            # read lifestyle from sql
            lifestyle_curr = pd.read_sql_query("""
                select lifestyle_item 
                from lifestyle 
                order by entry_time
            """, conn)

            # display with st.data_editor, which allows us to remove or edit items dynamically
            lifestyle_new = st.data_editor(
                lifestyle_curr,
                num_rows = "dynamic",
                column_config = {
                    "lifestyle_item": st.column_config.TextColumn(
                        "Lifestyle Item",
                        width = 275
                    )
                }
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Save Changes")

        if submit_button:
            # get updated list of to-do and date
            lifestyle = [
                (run_timestamp, lifestyle_item)
                for lifestyle_item
                in lifestyle_new["lifestyle_item"].tolist()
            ]

            # insert new items into table, ignoring existing ones 
            cursor.executemany("""
                insert into lifestyle (entry_time, lifestyle_item)
                values (%s, %s)
                on conflict (lifestyle_item) do nothing;
            """, lifestyle)
            cursor.execute("""
                insert into lifestyle_history (entry_time, action, lifestyle_item)
                select entry_time
                    ,'Added'
                    ,lifestyle_item
                from lifestyle
                on conflict (entry_time, action, lifestyle_item) do nothing;
            """)
            conn.commit()

            # pull any removed items  
            removed_lifestyle = [
                lifestyle_item
                for lifestyle_item
                in lifestyle_curr["lifestyle_item"].tolist()
                if lifestyle_item not in lifestyle_new["lifestyle_item"].tolist()
            ]

            # delete all removed items 
            if removed_lifestyle:
                placeholders = ", ".join("%s" for _ in removed_lifestyle)
                cursor.execute(
                    f"delete from lifestyle where lifestyle_item in ({placeholders})", removed_lifestyle
                )
                conn.commit()

                # get removed list of to-do and date
                lifestyle_removed = [
                    (run_timestamp, "Removed", lifestyle_item)
                    for lifestyle_item
                    in removed_lifestyle
                ]

                # insert removed items into table
                cursor.executemany("""
                    insert into lifestyle_history (entry_time, action, lifestyle_item)
                    values (%s, %s, %s)     
                    on conflict (entry_time, action, lifestyle_item) do nothing;
                """, lifestyle_removed)
                conn.commit()

            # rerun to pull updated data from database 
            st.session_state["lifestyle_update"] = True
            st.rerun()

        # display success message
        if st.session_state["lifestyle_update"]:
            st.success(f"[{run_timestamp}] Lifestyle updated!")
            st.session_state["lifestyle_update"] = False

            # level up relevant fish 
            current_date = datetime.strptime(run_timestamp, "%Y-%m-%d %I:%M:%S %p")
            _level_up_fish("Lifestyle", current_date.date(), conn)

    cursor.close()


def render_health(run_timestamp, conn):
    """
    Render section: Health
    This section can be used to document health metrics.
    """

    # display header: log my health!
    st.header("Health")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = False):
        with st.form("health_form", clear_on_submit = True, border = False):

            # offer various options for recording health:
            health_date = st.date_input(
                "Specify date:", 
                value = datetime.now(pytz.timezone(st.context.timezone)), 
                key = "health"
            )
            
            # select a metric type
            existing_health_metrics = pd.read_sql_query("""
                select distinct metric
                from health
                ;
            """, conn)
            health_metric = st.selectbox(
                "Enter metric type:",
                existing_health_metrics,
                accept_new_options = True,
            )

            # type text manually 
            health_text = st.text_input("Enter metric value:")

            # Forms require a dedicated submit button
            health_submit_button = st.form_submit_button("Submit Health")

        # conditional logic if button is clicked
        if health_submit_button:
            # save entry to database
            health_data = (
                run_timestamp, 
                health_date,
                health_metric,
                health_text
            )
            
            cursor.execute("""
                insert into health (entry_time, date, metric, value)
                values (%s, %s, %s, %s);
            """, health_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Health data recorded!")

            # level up relevant fish 
            _level_up_fish("Health", health_date, conn)

    cursor.close()


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

    
log()