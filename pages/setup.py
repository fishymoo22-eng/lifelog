import pandas as pd
from datetime import datetime

import streamlit as st
import psycopg
import pytz

from utilities.utilities import _write_text

def setup():
    """
    View setup instructions!
    """

    # record run time in relevant timezone
    user_timezone = pytz.timezone(st.context.timezone)
    run_timestamp = datetime.now(user_timezone).strftime("%Y-%m-%d %I:%M:%S %p")

    # initialize database connection
    conn = psycopg.connect(st.secrets["database"]["url"])

    # render sections
    st.title("Setup Guide")
    render_setup(run_timestamp, conn)

    # display last run date in gray
    _write_text(f":gray[Last run on: {run_timestamp}]")

    # close connection 
    conn.close()


def render_setup(run_timestamp, conn):
    """
    Render section: Setup.
    This section displays the setup guide.
    """
    
    # display header: instructions!
    st.header("Instructions")

    st.write(st.user)

    cursor = conn.cursor()

    cursor.close()


setup()