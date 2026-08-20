import pandas as pd
from datetime import datetime

import streamlit as st
import psycopg
import pytz

from utilities.utilities import _write_text

def insights():
    """
    View life insights!
    """

    # record run time in relevant timezone
    user_timezone = pytz.timezone(st.context.timezone)
    run_timestamp = datetime.now(user_timezone).strftime("%Y-%m-%d %I:%M:%S %p")

    # initialize database connection
    conn = psycopg.connect(st.secrets["database"]["url"])

    # render sections
    st.title("Life Insights")
    render_data(run_timestamp, conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


def render_data(run_timestamp, conn):
    """
    Render section: Data.
    This section allows the user to query the database data.
    """
    
    # display header: data!
    st.header("Data")

    cursor = conn.cursor()

    with st.expander("Click to expand/collapse", expanded = True):
        with st.form(key="configuration_form", border = False):
            # drop down list of table to query 
            from_table = st.selectbox(
                "Select a table:",
                ["to_do", "dreams", "activities", "journal", "reflections", "bingo_notes"],
            )

            # optional where clause 
            where_clause = st.text_input(
                "Optionally, enter a where condition:",
                "True"
            )

            # The app will only proceed past this line when the button is clicked
            submit_button = st.form_submit_button(label="Submit query")

        if submit_button:
            # check if table has entry_time field 
            f_entry_time = pd.read_sql_query(f"""
                select max(
                        case 
                            when column_name = 'entry_time' then 1 
                            else 0
                        end
                    ) as f_entry_time
                from information_schema.columns 
                where table_schema = 'public'
                    and table_name = '{from_table}'
            """, conn).loc[0, "f_entry_time"]

            # build order by clause on entry time, if available 
            if f_entry_time == 1:
                order_by_clause = "order by entry_time desc"
            else:
                order_by_clause = ""

            # query data 
            table_query_pd = pd.read_sql_query(f"""
                select * 
                from {from_table}
                where {where_clause}
                {order_by_clause}
            """, conn)

            st.success(f"[{run_timestamp}] Query executed!")
            st.dataframe(table_query_pd)

    cursor.close()


insights()