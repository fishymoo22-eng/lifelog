import streamlit as st

def main():
    """
    Log my life!
    """

    # configure app
    _configure_app()

    # define pages
    log_page = st.Page("pages/log.py", title = "Log")
    insights_page = st.Page("pages/insights.py", title = "Insights")
    recommendations_page = st.Page("pages/recommendations.py", title = "Recommendations")

    # pass to st.navigation
    pg = st.navigation([log_page, insights_page, recommendations_page])

    # run the selected page
    pg.run()


def _configure_app():
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

    # ensure initial sidebar is collapsed 
    st.set_page_config(initial_sidebar_state = "collapsed")

if __name__ == "__main__":
    main()