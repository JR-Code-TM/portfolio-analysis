import streamlit as st

from src.theme import apply_theme
from src import data_input, holdings, visualizations, risk_metrics


def init_session_state():
    if "holdings" not in st.session_state:
        st.session_state.holdings = []
    if "theme" not in st.session_state:
        st.session_state.theme = "light"
    if "price_cache" not in st.session_state:
        st.session_state.price_cache = {}


def main():
    st.set_page_config(
        page_title="Portfolio Analyzer",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    apply_theme()

    # Sidebar
    with st.sidebar:
        st.title("📈 Portfolio Analyzer")
        st.divider()

        # Theme toggle
        dark_mode = st.toggle(
            "Dark Mode",
            value=st.session_state.theme == "dark",
        )
        new_theme = "dark" if dark_mode else "light"
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

        st.divider()
        data_input.render_sidebar()

    # Main content
    st.title("Portfolio Analysis")

    if not st.session_state.holdings:
        st.info("Add holdings using the sidebar to get started.")

        st.subheader("How to get started")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
**Manual Entry**
1. Open the sidebar
2. Fill in ticker symbol, company, sector
3. Enter shares, current price, and cost basis
4. Click **Add Holding**
""")
        with c2:
            st.markdown("""
**CSV Import**
1. Prepare a CSV with columns for ticker, shares, price, cost basis
2. Open the *Import from CSV* section in the sidebar
3. Upload your file and map the columns
4. Click **Import Holdings**
""")
        return

    tab1, tab2, tab3 = st.tabs(["Holdings", "Performance", "Risk Metrics"])

    with tab1:
        holdings.render_table(st.session_state.holdings)

    with tab2:
        visualizations.render_charts(st.session_state.holdings)

    with tab3:
        risk_metrics.render_metrics(st.session_state.holdings)


if __name__ == "__main__":
    main()
