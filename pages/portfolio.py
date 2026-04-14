import streamlit as st

from src import data_input, holdings, visualizations, risk_metrics

# ---------------------------------------------------------------------------
# Sidebar — theme toggle + data entry
# ---------------------------------------------------------------------------
with st.sidebar:
    dark = st.toggle("Dark Mode", value=st.session_state.theme == "dark")
    new_theme = "dark" if dark else "light"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    st.divider()
    data_input.render_sidebar()

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------
st.title("💼 My Portfolio")

if not st.session_state.holdings:
    st.info("Add holdings using the sidebar to get started.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**Manual Entry**
1. Open the sidebar → *Add Holding Manually*
2. Type a ticker and click **Search** to auto-fill details
3. Enter your share count and optional cost basis
4. Click **Add Holding**
""")
    with c2:
        st.markdown("""
**CSV Import**
1. Open the sidebar → *Import from CSV*
2. Click **📥 Download sample template** — fill in Ticker, Shares, and optionally Cost Basis per Share
3. Upload your file and click **Import & Auto-load Holdings**
4. Company name, sector, country, price, and ETF status are fetched automatically
""")

else:
    tab1, tab2 = st.tabs(["Holdings & Performance", "Risk Metrics"])

    with tab1:
        holdings.render_table(st.session_state.holdings)
        st.divider()
        visualizations.render_charts(st.session_state.holdings)

    with tab2:
        risk_metrics.render_metrics(st.session_state.holdings)
