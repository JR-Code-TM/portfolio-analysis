import streamlit as st
import pandas as pd

from src.models import SECTORS


def render_sidebar():
    _render_manual_entry()
    _render_csv_upload()
    _render_controls()


def _render_manual_entry():
    with st.expander("Add Holding Manually", expanded=True):
        ticker = st.text_input("Ticker Symbol", placeholder="e.g. AAPL").upper().strip()
        company_name = st.text_input("Company Name", placeholder="e.g. Apple Inc.")
        sector = st.selectbox("Sector", options=SECTORS)
        shares = st.number_input("Shares", min_value=0.0, step=1.0, format="%.4f")
        price = st.number_input("Current Price ($)", min_value=0.0, step=0.01, format="%.2f")
        cost_basis = st.number_input("Cost Basis per Share ($)", min_value=0.0, step=0.01, format="%.2f")

        if st.button("Add Holding", type="primary", use_container_width=True):
            if not ticker:
                st.error("Ticker symbol is required.")
            elif shares <= 0:
                st.error("Shares must be greater than 0.")
            elif price <= 0:
                st.error("Price must be greater than 0.")
            elif cost_basis <= 0:
                st.error("Cost basis must be greater than 0.")
            else:
                holding = {
                    "ticker": ticker,
                    "company_name": company_name or ticker,
                    "sector": sector,
                    "shares": shares,
                    "price": price,
                    "cost_basis": cost_basis,
                }
                st.session_state.holdings.append(holding)
                st.session_state.price_cache = {}
                st.success(f"Added {ticker}")
                st.rerun()


def _render_csv_upload():
    with st.expander("Import from CSV"):
        uploaded_file = st.file_uploader("Upload CSV", type=["csv"], label_visibility="collapsed")

        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
            except Exception as e:
                st.error(f"Failed to read CSV: {e}")
                return

            st.caption("Preview (first 5 rows):")
            st.dataframe(df.head(), use_container_width=True)

            columns = ["-- Select --"] + list(df.columns)

            st.caption("Map CSV columns to required fields:")
            col_ticker = st.selectbox("Ticker", options=columns, key="csv_ticker")
            col_name = st.selectbox("Company Name", options=columns, key="csv_name")
            col_sector = st.selectbox("Sector", options=columns, key="csv_sector")
            col_shares = st.selectbox("Shares", options=columns, key="csv_shares")
            col_price = st.selectbox("Price", options=columns, key="csv_price")
            col_cost = st.selectbox("Cost Basis", options=columns, key="csv_cost")

            if st.button("Import Holdings", type="primary", use_container_width=True):
                required = {
                    "Ticker": col_ticker,
                    "Shares": col_shares,
                    "Price": col_price,
                    "Cost Basis": col_cost,
                }
                missing = [k for k, v in required.items() if v == "-- Select --"]
                if missing:
                    st.error(f"Please map required fields: {', '.join(missing)}")
                    return

                imported = 0
                errors = 0
                for idx, row in df.iterrows():
                    try:
                        ticker_val = str(row[col_ticker]).upper().strip()
                        if not ticker_val or ticker_val == "NAN":
                            continue

                        name_val = (
                            str(row[col_name]).strip()
                            if col_name != "-- Select --" and pd.notna(row.get(col_name))
                            else ticker_val
                        )
                        sector_val = (
                            str(row[col_sector]).strip()
                            if col_sector != "-- Select --" and pd.notna(row.get(col_sector))
                            else "Other"
                        )
                        shares_val = float(row[col_shares])
                        price_val = float(row[col_price])
                        cost_val = float(row[col_cost])

                        if shares_val <= 0 or price_val <= 0 or cost_val <= 0:
                            errors += 1
                            continue

                        st.session_state.holdings.append({
                            "ticker": ticker_val,
                            "company_name": name_val,
                            "sector": sector_val if sector_val in SECTORS else "Other",
                            "shares": shares_val,
                            "price": price_val,
                            "cost_basis": cost_val,
                        })
                        imported += 1
                    except (ValueError, KeyError):
                        errors += 1

                st.session_state.price_cache = {}
                if imported > 0:
                    st.success(f"Imported {imported} holdings.")
                if errors > 0:
                    st.warning(f"Skipped {errors} rows due to errors.")
                if imported > 0:
                    st.rerun()


def _render_controls():
    if st.session_state.holdings:
        st.divider()
        if st.button("Clear All Holdings", use_container_width=True):
            st.session_state.holdings = []
            st.session_state.price_cache = {}
            st.rerun()
