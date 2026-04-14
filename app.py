import streamlit as st

from src.theme import apply_theme


def init_session_state():
    defaults = {
        "holdings": [],
        "theme": "light",
        "price_cache": {},
        "ticker_info_cache": {},
        "etf_holdings_cache": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


st.set_page_config(
    page_title="Portfolio Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_session_state()
apply_theme()  # re-injected on every rerun — applies to all pages

pg = st.navigation(
    [
        st.Page("pages/portfolio.py", title="My Portfolio", icon="💼", default=True),
        st.Page("pages/research.py",  title="Stock Research", icon="🔍"),
    ],
    position="sidebar",
)
pg.run()
