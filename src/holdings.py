from __future__ import annotations

import streamlit as st
import pandas as pd


def render_table(holdings: list[dict]):
    if not holdings:
        st.info("No holdings yet. Add holdings using the sidebar.")
        return

    # Select only the columns we need — extra keys (country, is_etf) are ignored
    rows = [
        {
            "ticker": h.get("ticker", ""),
            "company_name": h.get("company_name", ""),
            "sector": h.get("sector", ""),
            "shares": h.get("shares", 0.0),
            "price": h.get("price"),
            "cost_basis": h.get("cost_basis"),
        }
        for h in holdings
    ]
    df = pd.DataFrame(rows)
    df.columns = ["Ticker", "Company", "Sector", "Shares", "Price", "Cost Basis"]

    # Coerce to numeric; non-numeric / None become NaN
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df["Cost Basis"] = pd.to_numeric(df["Cost Basis"], errors="coerce")
    df["Shares"] = pd.to_numeric(df["Shares"], errors="coerce")

    df["Market Value"] = df["Shares"] * df["Price"]
    df["Total Cost"] = df["Shares"] * df["Cost Basis"]
    df["Gain/Loss ($)"] = df["Market Value"] - df["Total Cost"]
    df["Gain/Loss (%)"] = (df["Gain/Loss ($)"] / df["Total Cost"]) * 100

    # Totals row (sum only non-NaN values)
    total_mv = df["Market Value"].sum(skipna=True)
    total_cost = df["Total Cost"].sum(skipna=True)
    total_gl = total_mv - total_cost
    total_pct = (total_gl / total_cost * 100) if total_cost > 0 else float("nan")

    totals = pd.DataFrame([{
        "Ticker": "TOTAL",
        "Company": "",
        "Sector": "",
        "Shares": float("nan"),
        "Price": float("nan"),
        "Cost Basis": float("nan"),
        "Market Value": total_mv,
        "Total Cost": total_cost if total_cost > 0 else float("nan"),
        "Gain/Loss ($)": total_gl if total_cost > 0 else float("nan"),
        "Gain/Loss (%)": total_pct,
    }])
    display_df = pd.concat([df, totals], ignore_index=True)

    col_config = {
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Company": st.column_config.TextColumn("Company"),
        "Sector": st.column_config.TextColumn("Sector"),
        "Shares": st.column_config.NumberColumn("Shares", format="%.2f"),
        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
        "Cost Basis": st.column_config.NumberColumn("Cost Basis", format="$%.2f"),
        "Market Value": st.column_config.NumberColumn("Market Value", format="$%.2f"),
        "Total Cost": st.column_config.NumberColumn("Total Cost", format="$%.2f"),
        "Gain/Loss ($)": st.column_config.NumberColumn("Gain/Loss ($)", format="$%.2f"),
        "Gain/Loss (%)": st.column_config.NumberColumn("Gain/Loss (%)", format="%.2f%%"),
    }

    st.dataframe(
        display_df,
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
    )

    missing_price = df["Price"].isna().any()
    missing_cost = df["Cost Basis"].isna().any()
    if missing_price:
        st.caption("— Price data unavailable for some holdings; market value shown as blank.")
    if missing_cost:
        st.caption("— Cost basis not provided for some holdings; gain/loss shown as blank.")

    # Summary cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Portfolio Value", f"${total_mv:,.2f}" if pd.notna(total_mv) else "N/A")
    if total_cost > 0 and pd.notna(total_gl):
        c2.metric("Total Gain/Loss", f"${total_gl:,.2f}", delta=f"{total_pct:.2f}%")
    else:
        c2.metric("Total Gain/Loss", "N/A")
    c3.metric("Total Cost Basis", f"${total_cost:,.2f}" if total_cost > 0 else "N/A")
