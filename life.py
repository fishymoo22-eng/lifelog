import streamlit as st
import numpy as np
import pandas as pd
import datetime
import psycopg

# log rerun 
run_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

# display title: log my life!
st.title("Life Log")

# first initialize sql connection
conn = psycopg.connect(st.secrets["database"]["url"])
cursor = conn.cursor()

# display header: log my things to remember!
st.header("Things to Remember")

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

# display header: log my dreams!
st.header("Dreams")

with st.expander("Click to expand/collapse", expanded = False):
    with st.form("dream_form", clear_on_submit = True, border = False):

        # offer various options for recording dreams:
        dream_date = st.date_input("Specify date, if applicable:", key = "dream")

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

# display title: log my journal!
st.header("Journal")

with st.expander("Click to expand/collapse", expanded = False):
    with st.form("journal_form", clear_on_submit = True, border = False):
        journal_date = st.date_input("Specify date, if applicable:", key = "journal")

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
        
        cursor = conn.cursor()
        cursor.execute("""
            insert into journal (entry_time, date, journal_text, file_name)
            values (%s, %s, %s, %s)
        """, journal_data)
        conn.commit()
        
        st.success(f"[{run_timestamp}] Journal data recorded!")

# display title: log my mood!
st.header("Mood")

with st.expander("Click to expand/collapse", expanded = False):
    with st.form("mood_form", clear_on_submit = True, border = False):

        mood_date = st.date_input("Specify date, if applicable:", key = "mood")

        # log how my day was
        general_day = st.radio(
            "How was your day?",
            ("Great :smiley:", "Good :blush:", "Okay :neutral_face:", "Bad :slightly_frowning_face:", "Terrible :sob:"),
            index = None,
            horizontal = True
        )

        # log descriptors for day
        st.write("What was it like?")
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
        
        cursor = conn.cursor()
        cursor.execute(
            "insert into mood values (%s, %s, %s, %s, %s)", mood_data
        )
        conn.commit()
        
        st.success(f"[{run_timestamp}] Mood data recorded!")

cursor.close()
conn.close()