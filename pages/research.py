import streamlit as st

from src import stock_analysis

# ---------------------------------------------------------------------------
# Sidebar — theme toggle only (no portfolio data entry here)
# ---------------------------------------------------------------------------
with st.sidebar:
    dark = st.toggle("Dark Mode", value=st.session_state.theme == "dark")
    new_theme = "dark" if dark else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("🔍 Stock Research")
stock_analysis.render_stock_analysis()
