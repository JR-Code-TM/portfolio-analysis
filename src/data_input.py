from __future__ import annotations

import streamlit as st
import pandas as pd

from src.models import SECTORS
from src.market_data import fetch_ticker_info


def render_sidebar():
    _render_manual_entry()
    _render_csv_upload()
    _render_controls()


# ---------------------------------------------------------------------------
# Manual entry
# ---------------------------------------------------------------------------

def _render_manual_entry():
    with st.expander("Add Holding Manually", expanded=True):
        # --- Ticker + Search (label sits above both columns so they start at same height) ---
        st.markdown("**Ticker Symbol**")
        t_col, btn_col = st.columns([3, 1.2])
        with t_col:
            ticker_input = st.text_input(
                "Ticker Symbol",
                placeholder="e.g. AAPL",
                key="manual_ticker_input",
                label_visibility="collapsed",
            ).upper().strip()
        with btn_col:
            lookup_clicked = st.button("Search", use_container_width=True)

        # Detect ticker change — clear stale lookup state
        if ticker_input != st.session_state.get("_last_lookup_ticker", ""):
            for k in ["_lookup_company", "_lookup_sector", "_lookup_country",
                      "_lookup_is_etf", "_last_lookup_ticker"]:
                st.session_state.pop(k, None)

        # Perform lookup
        if lookup_clicked and ticker_input:
            with st.spinner(f"Looking up {ticker_input}…"):
                info = fetch_ticker_info(ticker_input)
                # Store in persistent cache
                st.session_state.ticker_info_cache[ticker_input] = info

            if info["company_name"] is None and info["price"] is None:
                st.error(f"Could not find '{ticker_input}'. Check the symbol and try again.")
            else:
                st.session_state["_lookup_company"] = info["company_name"] or ticker_input
                st.session_state["_lookup_sector"] = info["sector"] or "Other"
                st.session_state["_lookup_country"] = info["country"] or ""
                st.session_state["_lookup_is_etf"] = info["is_etf"]
                st.session_state["_last_lookup_ticker"] = ticker_input
                st.rerun()

        is_etf = st.session_state.get("_lookup_is_etf", False)
        if is_etf:
            st.info("ETF detected — sector and country allocation will use underlying holdings.")

        # --- Editable pre-populated fields ---
        company_name = st.text_input(
            "Company Name",
            value=st.session_state.get("_lookup_company", ""),
            placeholder="Auto-filled after Lookup",
        )

        # Sector: pre-select from lookup if it matches a known sector
        lookup_sector = st.session_state.get("_lookup_sector", SECTORS[0])
        sector_default_idx = SECTORS.index(lookup_sector) if lookup_sector in SECTORS else len(SECTORS) - 1
        sector = st.selectbox("Sector", options=SECTORS, index=sector_default_idx)

        country = st.text_input(
            "Country",
            value=st.session_state.get("_lookup_country", ""),
            placeholder="Auto-filled after Lookup",
        )

        is_etf_override = st.checkbox(
            "This is an ETF",
            value=is_etf,
            help="When checked, holdings will be decomposed into underlying stocks for risk and allocation analysis.",
        )

        shares = st.number_input("Shares", min_value=0.0, step=1.0, format="%.4f")

        st.caption("Cost basis is optional — leave at 0 to skip gain/loss calculations.")
        cost_basis_val = st.number_input(
            "Cost Basis per Share ($)",
            min_value=0.0,
            step=0.01,
            format="%.2f",
            help="Your average purchase price per share. Leave at 0 to skip gain/loss.",
        )

        if st.button("Add Holding", type="primary", use_container_width=True):
            if not ticker_input:
                st.error("Ticker symbol is required.")
            elif shares <= 0:
                st.error("Shares must be greater than 0.")
            else:
                # Resolve price from cache (set during Lookup) or fetch now
                cached_info = st.session_state.ticker_info_cache.get(ticker_input, {})
                price = cached_info.get("price")

                if price is None:
                    with st.spinner(f"Fetching price for {ticker_input}…"):
                        fresh = fetch_ticker_info(ticker_input)
                        st.session_state.ticker_info_cache[ticker_input] = fresh
                        price = fresh.get("price")

                if price is None:
                    st.warning(f"Could not fetch price for {ticker_input}. It will show as N/A until data is available.")

                holding = {
                    "ticker": ticker_input,
                    "company_name": company_name or ticker_input,
                    "sector": sector,
                    "shares": shares,
                    "price": price,
                    "cost_basis": cost_basis_val if cost_basis_val > 0 else None,
                    "country": country.strip() or cached_info.get("country"),
                    "is_etf": is_etf_override,
                }
                st.session_state.holdings.append(holding)
                st.session_state.price_cache = {}

                # Clear lookup state
                for k in ["_lookup_company", "_lookup_sector", "_lookup_country",
                          "_lookup_is_etf", "_last_lookup_ticker"]:
                    st.session_state.pop(k, None)

                st.success(f"Added {ticker_input}" + (f" @ ${price:.2f}" if price else ""))
                st.rerun()


# ---------------------------------------------------------------------------
# CSV upload
# ---------------------------------------------------------------------------

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

            st.caption("Map CSV columns to required fields (* = required):")
            col_ticker = st.selectbox("Ticker *", options=columns, key="csv_ticker")
            col_shares = st.selectbox("Shares *", options=columns, key="csv_shares")
            col_name = st.selectbox("Company Name (optional)", options=columns, key="csv_name")
            col_sector = st.selectbox("Sector (optional)", options=columns, key="csv_sector")
            col_cost = st.selectbox("Cost Basis (optional)", options=columns, key="csv_cost")
            col_country = st.selectbox("Country (optional)", options=columns, key="csv_country")

            if st.button("Import Holdings", type="primary", use_container_width=True):
                required = {"Ticker": col_ticker, "Shares": col_shares}
                missing = [k for k, v in required.items() if v == "-- Select --"]
                if missing:
                    st.error(f"Please map required fields: {', '.join(missing)}")
                    return

                imported = errors = 0
                for _, row in df.iterrows():
                    try:
                        ticker_val = str(row[col_ticker]).upper().strip()
                        if not ticker_val or ticker_val == "NAN":
                            continue

                        shares_val = float(row[col_shares])
                        if shares_val <= 0:
                            errors += 1
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
                        cost_val_raw = (
                            float(row[col_cost])
                            if col_cost != "-- Select --" and pd.notna(row.get(col_cost))
                            else 0.0
                        )
                        country_val = (
                            str(row[col_country]).strip()
                            if col_country != "-- Select --" and pd.notna(row.get(col_country))
                            else None
                        )

                        st.session_state.holdings.append({
                            "ticker": ticker_val,
                            "company_name": name_val,
                            "sector": sector_val if sector_val in SECTORS else "Other",
                            "shares": shares_val,
                            "price": None,   # will be fetched when charts/metrics render
                            "cost_basis": cost_val_raw if cost_val_raw > 0 else None,
                            "country": country_val,
                            "is_etf": False,
                        })
                        imported += 1
                    except (ValueError, KeyError):
                        errors += 1

                st.session_state.price_cache = {}
                if imported > 0:
                    st.success(f"Imported {imported} holdings. Prices will be fetched automatically.")
                if errors > 0:
                    st.warning(f"Skipped {errors} rows due to errors.")
                if imported > 0:
                    st.rerun()


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

def _render_controls():
    if st.session_state.holdings:
        st.divider()
        if st.button("Clear All Holdings", use_container_width=True):
            st.session_state.holdings = []
            st.session_state.price_cache = {}
            st.rerun()
