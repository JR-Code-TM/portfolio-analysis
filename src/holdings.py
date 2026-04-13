import streamlit as st
import pandas as pd


def render_table(holdings: list[dict]):
    if not holdings:
        st.info("No holdings yet. Add holdings using the sidebar.")
        return

    df = pd.DataFrame(holdings)
    df.columns = ["Ticker", "Company", "Sector", "Shares", "Price", "Cost Basis"]

    df["Market Value"] = df["Shares"] * df["Price"]
    df["Total Cost"] = df["Shares"] * df["Cost Basis"]
    df["Gain/Loss ($)"] = df["Market Value"] - df["Total Cost"]
    df["Gain/Loss (%)"] = (df["Gain/Loss ($)"] / df["Total Cost"]) * 100

    total_mv = df["Market Value"].sum()
    total_cost = df["Total Cost"].sum()
    total_gl = total_mv - total_cost
    total_pct = (total_gl / total_cost * 100) if total_cost > 0 else 0.0

    totals = pd.DataFrame([{
        "Ticker": "TOTAL",
        "Company": "",
        "Sector": "",
        "Shares": "",
        "Price": "",
        "Cost Basis": "",
        "Market Value": total_mv,
        "Total Cost": total_cost,
        "Gain/Loss ($)": total_gl,
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

    # Summary cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Portfolio Value", f"${total_mv:,.2f}")
    c2.metric("Total Gain/Loss", f"${total_gl:,.2f}", delta=f"{total_pct:.2f}%")
    c3.metric("Total Cost Basis", f"${total_cost:,.2f}")
