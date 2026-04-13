import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.theme import get_plotly_template, get_plotly_bg_color
from src.market_data import fetch_price_history, fetch_benchmark


def render_charts(holdings: list[dict]):
    if not holdings:
        st.info("No holdings yet. Add holdings using the sidebar.")
        return

    tickers = list({h["ticker"] for h in holdings})

    with st.spinner("Loading market data..."):
        price_data, synthetic_tickers = fetch_price_history(tickers)
        benchmark = fetch_benchmark()

    col1, col2 = st.columns([2, 1])

    with col1:
        _render_performance_chart(holdings, price_data, benchmark, synthetic_tickers)

    with col2:
        _render_sector_pie(holdings)


def _render_performance_chart(
    holdings: list[dict],
    price_data: dict[str, pd.Series],
    benchmark: pd.Series,
    synthetic_tickers: list[str],
):
    st.subheader("Portfolio Performance vs S&P 500")

    # Build portfolio value series (daily total value)
    all_dates = benchmark.index
    for series in price_data.values():
        all_dates = all_dates.union(series.index)
    all_dates = all_dates.sort_values()

    # Forward-fill each ticker's prices to common date index
    aligned = {}
    for ticker, series in price_data.items():
        aligned[ticker] = series.reindex(all_dates).ffill().bfill()

    bench_aligned = benchmark.reindex(all_dates).ffill().bfill()

    # Compute daily portfolio value
    portfolio_value = pd.Series(0.0, index=all_dates)
    for h in holdings:
        ticker = h["ticker"]
        if ticker in aligned:
            portfolio_value += h["shares"] * aligned[ticker]

    # Normalize to base 100
    if portfolio_value.iloc[0] != 0:
        portfolio_norm = portfolio_value / portfolio_value.iloc[0] * 100
    else:
        portfolio_norm = portfolio_value

    bench_norm = bench_aligned / bench_aligned.iloc[0] * 100

    template = get_plotly_template()
    bg_color = get_plotly_bg_color()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_norm.index,
        y=portfolio_norm.values,
        name="Portfolio",
        line=dict(color="#2962ff", width=2.5),
    ))
    fig.add_trace(go.Scatter(
        x=bench_norm.index,
        y=bench_norm.values,
        name="S&P 500",
        line=dict(color="#ff6d00", width=2, dash="dash"),
    ))

    fig.update_layout(
        template=template,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        yaxis_title="Normalized Value (Base 100)",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True)

    if synthetic_tickers:
        st.caption(f"* Simulated data used for: {', '.join(synthetic_tickers)}")


def _render_sector_pie(holdings: list[dict]):
    st.subheader("Sector Allocation")

    sector_values = {}
    for h in holdings:
        mv = h["shares"] * h["price"]
        sector_values[h["sector"]] = sector_values.get(h["sector"], 0) + mv

    sectors = list(sector_values.keys())
    values = list(sector_values.values())

    template = get_plotly_template()
    bg_color = get_plotly_bg_color()

    fig = px.pie(
        names=sectors,
        values=values,
        hole=0.4,
        template=template,
    )
    fig.update_layout(
        paper_bgcolor=bg_color,
        margin=dict(l=20, r=20, t=20, b=20),
        height=420,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05),
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")

    st.plotly_chart(fig, use_container_width=True)
