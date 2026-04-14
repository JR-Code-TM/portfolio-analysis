import streamlit as st

from src import stock_analysis

# ---------------------------------------------------------------------------
# Clear state when navigating TO this page from another page.
# _on_research_page is set to False by other pages; when we see it as False
# (or absent) on entry, we know the user just arrived and should reset.
# ---------------------------------------------------------------------------
if not st.session_state.get("_on_research_page", False):
    st.session_state.pop("sa_last_ticker", None)
    st.session_state["sa_ticker_input"] = ""
    st.session_state["_on_research_page"] = True

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
st.title("🔍 Equity Research")
stock_analysis.render_stock_analysis()
