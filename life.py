import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import psycopg
import pytz


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
    render_things_to_remember(run_timestamp, conn)
    render_dreams(run_timestamp, conn)
    render_activities(run_timestamp, conn)
    render_journal(run_timestamp, conn)
    render_mood(run_timestamp, conn)
    
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

        with st.form(key="things_to_remember_form", border=False):
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
                        "thing_to_remember",
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
            dream_date = st.date_input("Specify date:", key = "dream")

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

        # save the captured input on click
        if dream_submit_button:
            # save entry to database
            dream_data = (
                run_timestamp, 
                dream_date,
                dream_text,
                audio_file,
            )
            
            cursor.execute("""
                insert into dreams (entry_time, date, dream_text, file_name)
                values (%s, %s, %s, %s);
            """, dream_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Dream data recorded!")

    cursor.close()


def render_activities(run_timestamp, conn):
    """
    Render section: Activities
    This section can be used to document activities through the day.
    """

    # display title: log my activities!
    st.header("Activities")

    cursor = conn.cursor()

    # define list of activity options
    activity_menu = {
        "Develop Life Log :computer:": {
            "selected": False
        },
        "Go on a walk :walking_man:": {
            "selected": False
        },
        "Play catch :baseball:": {
            "selected": False
        },
        "Play basketball :basketball:": {
            "selected": False
        },
        "Play on swingset :chains:": {
            "selected": False
        },
        "Read :open_book:": {
            "selected": False
        },
        "Dance :dancer:": {
            "selected": False
        },
        "Watch TV :tv:": {
            "selected": False
        },
        "Watch a movie :movie_camera:": {
            "selected": False
        },
    }

    with st.expander("Click to expand/collapse", expanded = False):
        activity_date = st.date_input("Specify date:", key = "activity")

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
            _write_text("Rate eventual enjoyment of activities:")
                
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
            
        # display button to push to database
        activities_submit_button = st.button("Submit Activities")

        # save the captured input on click
        if activities_submit_button and f_selected_activities:
            # save activities to database
            activity_data = [
                (
                    run_timestamp,
                    activity_date,
                    activity_text,
                    activity_menu[activity_text]["resistance"],
                    activity_menu[activity_text]["enjoyment"]
                )
                for activity_text 
                in activity_menu
                if activity_menu[activity_text]["selected"]
            ]
            
            cursor.executemany("""
                insert into activities (entry_time, date, activity, resistance_rating, enjoyment_rating)
                values (%s, %s, %s, %s, %s)
            """, activity_data)
            conn.commit()
            
            st.success(f"[{run_timestamp}] Activity data recorded!")
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
            journal_date = st.date_input("Specify date:", key = "journal")

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

        # save the captured input on click
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

            mood_date = st.date_input("Specify date:", key = "mood")

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

        # save the captured input on click
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