import streamlit as st 

def _write_text(
    text: str,
    size: str = "14"
):
    """
    Display text with custom font size to match Streamlit labels.
    """
    return st.markdown(f"<span style='font-size: {size}px;'>{text}</span>", unsafe_allow_html = True)
