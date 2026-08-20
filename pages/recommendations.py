import pandas as pd
from datetime import datetime

import streamlit as st
import psycopg
import pytz
import random

from utilities.utilities import _write_text

def recommendations():
    """
    Life recommendations!
    """

    # record run time in relevant timezone
    user_timezone = pytz.timezone(st.context.timezone)
    run_timestamp = datetime.now(user_timezone).strftime("%Y-%m-%d %I:%M:%S %p")

    # initialize database connection
    conn = psycopg.connect(st.secrets["database"]["url"])

    # render sections
    st.title("Life Recommendations")    
    render_activity_roll(run_timestamp, conn)
    configure_user_options(run_timestamp, conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


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


recommendations()