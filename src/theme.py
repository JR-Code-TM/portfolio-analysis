import streamlit as st

DARK_CSS = """
<style>
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"] {
        background-color: #0e1117 !important;
        color: #fafafa !important;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #0e1117 !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #fafafa !important;
    }
    [data-testid="stMetric"] {
        background-color: #161b22 !important;
        border-radius: 8px;
        padding: 12px;
    }
    .stDataFrame, .stTable {
        background-color: #161b22 !important;
    }
    p, span, label, .stMarkdown, h1, h2, h3, h4, h5, h6 {
        color: #fafafa !important;
    }
    [data-testid="stExpander"] {
        background-color: #161b22 !important;
        border-color: #30363d !important;
    }
    [data-testid="stSidebar"] .stButton button {
        white-space: nowrap !important;
    }
</style>
"""

LIGHT_CSS = """
<style>
    [data-testid="stMetric"] {
        background-color: #f8f9fa !important;
        border-radius: 8px;
        padding: 12px;
    }
    [data-testid="stSidebar"] .stButton button {
        white-space: nowrap !important;
    }
</style>
"""


def apply_theme():
    theme = st.session_state.get("theme", "light")
    if theme == "dark":
        st.markdown(DARK_CSS, unsafe_allow_html=True)
    else:
        st.markdown(LIGHT_CSS, unsafe_allow_html=True)


def get_plotly_template() -> str:
    theme = st.session_state.get("theme", "light")
    return "plotly_dark" if theme == "dark" else "plotly_white"


def get_plotly_bg_color() -> str:
    theme = st.session_state.get("theme", "light")
    return "#0e1117" if theme == "dark" else "#ffffff"
