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
    render_data(conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


def render_data(conn):
    """
    Render section: Data.
    This section allows the user to query the database data.
    """
    
    # display header: data!
    st.header("Data")

    cursor = conn.cursor()

    _write_text("hello")

    cursor.close()


insights()