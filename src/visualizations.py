from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.theme import get_plotly_template, get_plotly_bg_color
from src.market_data import (
    fetch_price_history,
    fetch_benchmark,
    get_etf_holdings_cached,
    expand_holdings_for_analysis,
)

# ---------------------------------------------------------------------------
# Region mapping
# ---------------------------------------------------------------------------

COUNTRY_TO_REGION: dict[str, str] = {
    # North America
    "United States": "North America", "US": "North America", "USA": "North America",
    "Canada": "North America", "Mexico": "North America",
    # Latin America
    "Brazil": "Latin America", "Argentina": "Latin America", "Chile": "Latin America",
    "Colombia": "Latin America", "Peru": "Latin America", "Venezuela": "Latin America",
    "Ecuador": "Latin America", "Bolivia": "Latin America", "Paraguay": "Latin America",
    "Uruguay": "Latin America", "Panama": "Latin America", "Costa Rica": "Latin America",
    "Guatemala": "Latin America", "Dominican Republic": "Latin America",
    # Europe
    "United Kingdom": "Europe", "Germany": "Europe", "France": "Europe",
    "Italy": "Europe", "Spain": "Europe", "Netherlands": "Europe",
    "Switzerland": "Europe", "Sweden": "Europe", "Norway": "Europe",
    "Denmark": "Europe", "Finland": "Europe", "Belgium": "Europe",
    "Austria": "Europe", "Portugal": "Europe", "Ireland": "Europe",
    "Poland": "Europe", "Russia": "Europe", "Czech Republic": "Europe",
    "Hungary": "Europe", "Greece": "Europe", "Luxembourg": "Europe",
    "Romania": "Europe", "Slovakia": "Europe", "Croatia": "Europe",
    # Middle East
    "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East",
    "UAE": "Middle East", "Israel": "Middle East", "Qatar": "Middle East",
    "Kuwait": "Middle East", "Bahrain": "Middle East", "Turkey": "Middle East",
    "Jordan": "Middle East", "Oman": "Middle East", "Lebanon": "Middle East",
    # Africa
    "South Africa": "Africa", "Nigeria": "Africa", "Kenya": "Africa",
    "Egypt": "Africa", "Morocco": "Africa", "Ghana": "Africa",
    "Ethiopia": "Africa", "Tanzania": "Africa", "Zimbabwe": "Africa",
    # APAC
    "Japan": "APAC", "China": "APAC", "Hong Kong": "APAC", "Australia": "APAC",
    "South Korea": "APAC", "India": "APAC", "Singapore": "APAC", "Taiwan": "APAC",
    "New Zealand": "APAC", "Indonesia": "APAC", "Malaysia": "APAC",
    "Thailand": "APAC", "Philippines": "APAC", "Vietnam": "APAC",
    "Bangladesh": "APAC", "Pakistan": "APAC", "Sri Lanka": "APAC",
    "Myanmar": "APAC", "Cambodia": "APAC",
}

# Keyword-based fallback for ETFs where country is not available
ETF_NAME_KEYWORDS: dict[str, list[str]] = {
    "APAC": [
        "japan", "china", "asia", "pacific", "apac", "korea", "india", "australia",
        "singapore", "taiwan", "hong kong", "emerging asia", "msci asia",
    ],
    "Europe": [
        "europe", "european", "ftse europe", "stoxx", "euro", "eurozone",
        "msci europe", "pan european",
    ],
    "Middle East": [
        "middle east", "gulf", "mena", "saudi", "emerging markets middle", "gcc",
    ],
    "Africa": ["africa", "african"],
    "Latin America": [
        "latin america", "latin", "latam", "brazil", "emerging americas",
        "msci latin",
    ],
    "North America": [
        "north america", "s&p 500", "nasdaq", "dow jones", "russell", "us equity",
        "american", "united states",
    ],
}


def _get_region(holding: dict) -> str:
    """Map a holding to one of the 6 finance regions."""
    country = holding.get("country")
    if country:
        return COUNTRY_TO_REGION.get(country, "Other")
    # Fallback for ETFs without a country: keyword-match the company name
    name = (holding.get("company_name") or holding.get("ticker", "")).lower()
    for region, keywords in ETF_NAME_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return region
    return "Other"


# ---------------------------------------------------------------------------
# Public render entry point
# ---------------------------------------------------------------------------

def render_charts(holdings: list[dict]):
    if not holdings:
        st.info("No holdings yet. Add holdings using the sidebar.")
        return

    # Collect all tickers: base holdings + ETF sub-holdings
    base_tickers = list({h["ticker"] for h in holdings})
    sub_tickers = [
        sub["ticker"]
        for h in holdings if h.get("is_etf", False)
        for sub in get_etf_holdings_cached(h["ticker"])
    ]
    all_tickers = tuple(set(base_tickers + sub_tickers))

    with st.spinner("Loading market data…"):
        price_data, synthetic_tickers = fetch_price_history(all_tickers)
        benchmark = fetch_benchmark()

    # Expand ETF holdings for composition charts
    expanded = expand_holdings_for_analysis(holdings, price_data)

    # Row 1: performance chart (full width)
    _render_performance_chart(holdings, price_data, benchmark, synthetic_tickers)

    # Row 2: sector + region pies side by side
    col1, col2 = st.columns(2)
    with col1:
        _render_sector_pie(expanded)
    with col2:
        _render_region_pie(expanded)


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

def _render_performance_chart(
    holdings: list[dict],
    price_data: dict[str, pd.Series],
    benchmark: pd.Series,
    synthetic_tickers: list[str],
):
    st.subheader("Portfolio Performance vs S&P 500")

    # Build common date index
    all_dates = benchmark.index
    for series in price_data.values():
        all_dates = all_dates.union(series.index)
    all_dates = all_dates.sort_values()

    aligned = {
        ticker: series.reindex(all_dates).ffill().bfill()
        for ticker, series in price_data.items()
    }
    bench_aligned = benchmark.reindex(all_dates).ffill().bfill()

    # Compute daily portfolio value using original (non-expanded) holdings
    portfolio_value = pd.Series(0.0, index=all_dates)
    for h in holdings:
        ticker = h["ticker"]
        if ticker in aligned:
            portfolio_value += h["shares"] * aligned[ticker]

    if portfolio_value.iloc[0] == 0:
        st.warning("Could not compute portfolio performance — no price data available.")
        return

    portfolio_norm = portfolio_value / portfolio_value.iloc[0] * 100
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
        yaxis_title="Normalised Value (Base 100)",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
        height=420,
    )

    st.plotly_chart(fig, use_container_width=True)

    if synthetic_tickers:
        st.caption(f"* Simulated data used for: {', '.join(synthetic_tickers)}")


def _render_sector_pie(expanded_holdings: list[dict]):
    st.subheader("Sector Allocation")

    sector_values: dict[str, float] = {}
    for h in expanded_holdings:
        price = h.get("price")
        if price is None:
            continue
        mv = h["shares"] * price
        sector = h.get("sector") or "Other"
        sector_values[sector] = sector_values.get(sector, 0.0) + mv

    if not sector_values:
        st.info("No sector data available.")
        return

    _render_donut(list(sector_values.keys()), list(sector_values.values()))


def _render_region_pie(expanded_holdings: list[dict]):
    st.subheader("Regional Exposure")

    region_values: dict[str, float] = {}
    for h in expanded_holdings:
        price = h.get("price")
        if price is None:
            continue
        mv = h["shares"] * price
        region = _get_region(h)
        region_values[region] = region_values.get(region, 0.0) + mv

    if not region_values:
        st.info("Regional data unavailable. Use Search when adding holdings to populate country data.")
        return

    _render_donut(list(region_values.keys()), list(region_values.values()))


def _render_donut(names: list[str], values: list[float]):
    template = get_plotly_template()
    bg_color = get_plotly_bg_color()

    fig = px.pie(
        names=names,
        values=values,
        hole=0.4,
        template=template,
    )
    fig.update_layout(
        paper_bgcolor=bg_color,
        margin=dict(l=20, r=20, t=20, b=20),
        height=380,
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.05),
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig, use_container_width=True)
