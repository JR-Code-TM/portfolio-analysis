"""Stock Analysis tab — per-ticker deep-dive with financial metrics,
analyst recommendations, price chart, and latest news.
"""
from __future__ import annotations

import datetime
from typing import Any, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

from src.theme import get_plotly_template, get_plotly_bg_color


# ---------------------------------------------------------------------------
# Cached data-fetch helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def _fetch_info(ticker: str) -> dict:
    """Fetch yf.Ticker(ticker).info dict; returns {} on any failure."""
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=300)
def _fetch_history(ticker: str) -> pd.DataFrame:
    """Fetch 1-year OHLCV DataFrame; returns empty DataFrame on failure."""
    try:
        df = yf.Ticker(ticker).history(period="1y")
        return df if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300)
def _fetch_news(ticker: str) -> list[dict]:
    """Fetch latest news items; returns [] on failure."""
    try:
        return yf.Ticker(ticker).news or []
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Formatting utilities
# ---------------------------------------------------------------------------

def _fmt(value: Any, fmt: str = "") -> str:
    """Format a numeric value or return 'N/A' if None/unparseable.

    fmt options:
        "dollar"  — $1,234.56
        "large"   — abbreviate to $1.23B / $456.78M / $1.23T
        "pct"     — multiply by 100 and show as X.XX%  (value is a decimal, e.g. 0.25)
        "x"       — X.XXx  (for multiples like P/E)
        ""        — plain str
    """
    if value is None:
        return "N/A"
    try:
        v = float(value)
        if fmt == "dollar":
            return f"${v:,.2f}"
        if fmt == "large":
            if abs(v) >= 1e12:
                return f"${v / 1e12:.2f}T"
            if abs(v) >= 1e9:
                return f"${v / 1e9:.2f}B"
            if abs(v) >= 1e6:
                return f"${v / 1e6:.2f}M"
            return f"${v:,.0f}"
        if fmt == "pct":
            return f"{v * 100:.2f}%"
        if fmt == "pct_raw":   # value is already in percent units (e.g. yfinance dividendYield in v1.2+)
            return f"{v:.2f}%"
        if fmt == "x":
            return f"{v:.2f}x"
        return f"{v:,.4g}"
    except (TypeError, ValueError):
        return "N/A"


def _time_ago(pub_date) -> str:
    """Convert a pubDate (ISO string or Unix timestamp) to a relative string."""
    if not pub_date:
        return ""
    try:
        if isinstance(pub_date, str):
            dt = datetime.datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
        else:
            dt = datetime.datetime.fromtimestamp(int(pub_date), tz=datetime.timezone.utc)
        delta = datetime.datetime.now(tz=datetime.timezone.utc) - dt
        days = delta.days
        if days == 0:
            hours = delta.seconds // 3600
            return f"{hours}h ago" if hours > 0 else "Just now"
        if days == 1:
            return "Yesterday"
        return f"{days} days ago"
    except Exception:
        return ""


def _recommendation_color(key: Optional[str]) -> str:
    mapping = {
        "strong_buy": "#26a69a",
        "buy": "#26a69a",
        "hold": "#ff6d00",
        "underperform": "#ef5350",
        "sell": "#ef5350",
    }
    return mapping.get((key or "").lower(), "#888888")


def _recommendation_label(key: Optional[str]) -> str:
    return (key or "N/A").replace("_", " ").title()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_stock_analysis():
    """Render the Stock Analysis tab."""
    st.subheader("📈 Stock Analysis")

    col_input, col_btn = st.columns([4, 1])
    with col_input:
        ticker_raw = st.text_input(
            "Ticker Symbol",
            placeholder="e.g. AAPL, MSFT, VOO",
            key="sa_ticker_input",
            label_visibility="collapsed",
        )
    with col_btn:
        analyze = st.button("Analyze", type="primary", use_container_width=True)

    ticker = ticker_raw.upper().strip()

    # Persist the last analyzed ticker across tab switches
    if analyze and ticker:
        st.session_state["sa_last_ticker"] = ticker
        # Clear cache key so a fresh analysis is triggered on explicit re-analyze
        _fetch_info.clear()
        _fetch_history.clear()
        _fetch_news.clear()

    active_ticker = st.session_state.get("sa_last_ticker")

    if not active_ticker:
        st.info("Enter a ticker symbol above and click **Analyze** to get started.")
        return

    _render_analysis(active_ticker)


# ---------------------------------------------------------------------------
# Analysis orchestrator
# ---------------------------------------------------------------------------

def _render_analysis(ticker: str):
    with st.spinner(f"Fetching data for **{ticker}**…"):
        info = _fetch_info(ticker)
        hist = _fetch_history(ticker)
        news = _fetch_news(ticker)

    # Guard: detect empty / invalid ticker
    company = info.get("longName") or info.get("shortName")
    if not company and hist.empty:
        st.error(
            f"Could not retrieve data for **'{ticker}'**. "
            "Please verify the ticker symbol and try again."
        )
        return

    _render_header(ticker, info)
    st.divider()
    _render_key_metrics(info)
    st.divider()
    _render_recommendation(info)
    st.divider()
    _render_financial_metrics(info)
    st.divider()
    _render_price_chart(ticker, hist)
    st.divider()
    _render_news(news)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_header(ticker: str, info: dict):
    company_name = info.get("longName") or info.get("shortName") or ticker
    exchange = info.get("exchange") or info.get("fullExchangeName") or ""
    sector = info.get("sector") or ""
    industry = info.get("industry") or ""
    summary = info.get("longBusinessSummary") or ""

    st.markdown(f"## {company_name} &nbsp; `{ticker}`")

    meta_parts = []
    if exchange:
        meta_parts.append(f"Exchange: **{exchange}**")
    if sector:
        meta_parts.append(f"Sector: **{sector}**")
    if industry:
        meta_parts.append(f"Industry: **{industry}**")
    if meta_parts:
        st.caption(" | ".join(meta_parts))

    if summary:
        display = summary if len(summary) <= 500 else summary[:497] + "…"
        st.markdown(display)


def _render_key_metrics(info: dict):
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
    day_change_pct: Optional[float] = None
    if price and prev_close and prev_close != 0:
        day_change_pct = (price - prev_close) / prev_close * 100

    market_cap = info.get("marketCap")
    pe_trailing = info.get("trailingPE")
    pe_forward = info.get("forwardPE")
    week_low = info.get("fiftyTwoWeekLow")
    week_high = info.get("fiftyTwoWeekHigh")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(
        "Current Price",
        _fmt(price, "dollar"),
        delta=f"{day_change_pct:+.2f}%" if day_change_pct is not None else None,
    )
    c2.metric("Market Cap", _fmt(market_cap, "large"))
    c3.metric("P/E (Trailing)", _fmt(pe_trailing, "x"))
    c4.metric("Forward P/E", _fmt(pe_forward, "x"))
    c5.metric("52W Low", _fmt(week_low, "dollar"))
    c6.metric("52W High", _fmt(week_high, "dollar"))


def _render_recommendation(info: dict):
    st.subheader("Analyst Recommendation")

    rec_key = info.get("recommendationKey")
    rec_mean = info.get("recommendationMean")
    num_analysts = info.get("numberOfAnalystOpinions")
    target_price = info.get("targetMeanPrice")
    target_low = info.get("targetLowPrice")
    target_high = info.get("targetHighPrice")
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    color = _recommendation_color(rec_key)
    label = _recommendation_label(rec_key)

    st.markdown(
        f"<span style='font-size:1.6rem; font-weight:700; color:{color}'>{label}</span>",
        unsafe_allow_html=True,
    )

    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric(
        "Consensus Score",
        f"{rec_mean:.1f} / 5.0" if rec_mean is not None else "N/A",
        help="1 = Strong Buy · 3 = Hold · 5 = Strong Sell",
    )
    r2.metric("# Analysts", str(num_analysts) if num_analysts else "N/A")
    r3.metric("Mean Target", _fmt(target_price, "dollar"))
    r4.metric("Target Low", _fmt(target_low, "dollar"))
    r5.metric("Target High", _fmt(target_high, "dollar"))

    if target_price and current_price and current_price > 0:
        upside_pct = (target_price - current_price) / current_price * 100
        direction = "upside" if upside_pct >= 0 else "downside"
        arrow = "▲" if upside_pct >= 0 else "▼"
        st.caption(
            f"{arrow} Mean analyst target implies **{abs(upside_pct):.1f}% {direction}** "
            f"vs current price of {_fmt(current_price, 'dollar')}."
        )


def _render_financial_metrics(info: dict):
    st.subheader("Financial Metrics")

    left, right = st.columns(2)

    def _row(col, label: str, value: str):
        lc, vc = col.columns([2, 1])
        lc.markdown(f"**{label}**")
        vc.markdown(value)

    with left:
        st.markdown("**Growth & Profitability**")
        _row(left, "Revenue Growth (YoY)", _fmt(info.get("revenueGrowth"), "pct"))
        _row(left, "Earnings Growth",       _fmt(info.get("earningsGrowth"), "pct"))
        _row(left, "Profit Margin",         _fmt(info.get("profitMargins"), "pct"))
        _row(left, "Return on Equity",      _fmt(info.get("returnOnEquity"), "pct"))
        _row(left, "Return on Assets",      _fmt(info.get("returnOnAssets"), "pct"))
        _row(left, "Debt / Equity",         _fmt(info.get("debtToEquity")))
        _row(left, "Current Ratio",         _fmt(info.get("currentRatio")))
        _row(left, "Dividend Yield",        _fmt(info.get("dividendYield"), "pct_raw"))
        _row(left, "Beta",                  _fmt(info.get("beta")))

    with right:
        st.markdown("**Valuation & Per-Share**")
        _row(right, "EPS (TTM)",        _fmt(info.get("trailingEps"), "dollar"))
        _row(right, "Forward EPS",      _fmt(info.get("forwardEps"), "dollar"))
        _row(right, "Book Value",       _fmt(info.get("bookValue"), "dollar"))
        _row(right, "Price / Book",     _fmt(info.get("priceToBook"), "x"))
        _row(right, "EV / EBITDA",      _fmt(info.get("enterpriseToEbitda"), "x"))
        _row(right, "EV / Revenue",     _fmt(info.get("enterpriseToRevenue"), "x"))
        fcf = info.get("freeCashflow")
        _row(right, "Free Cash Flow",   _fmt(fcf, "large") if fcf is not None else "N/A")
        _row(right, "Payout Ratio",     _fmt(info.get("payoutRatio"), "pct"))
        _row(right, "Short % of Float", _fmt(info.get("shortPercentOfFloat"), "pct"))


def _render_price_chart(ticker: str, hist: pd.DataFrame):
    st.subheader("1-Year Price History")

    if hist.empty:
        st.warning("Price history data is unavailable for this ticker.")
        return

    # Flatten potential MultiIndex columns (yfinance sometimes returns them)
    close = hist["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close = close.dropna()

    ma50 = close.rolling(window=50).mean()
    ma200 = close.rolling(window=200).mean()

    template = get_plotly_template()
    bg_color = get_plotly_bg_color()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=close.index,
        y=close.values,
        name=f"{ticker} Close",
        line=dict(color="#2962ff", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=ma50.index,
        y=ma50.values,
        name="50-Day MA",
        line=dict(color="#ff6d00", width=1.5, dash="dot"),
    ))
    fig.add_trace(go.Scatter(
        x=ma200.index,
        y=ma200.values,
        name="200-Day MA",
        line=dict(color="#26a69a", width=1.5, dash="dash"),
    ))

    fig.update_layout(
        template=template,
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        yaxis_title="Price (USD)",
        xaxis_title="",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Quick technical signal based on moving averages
    if not ma50.dropna().empty and not ma200.dropna().empty:
        last_close = close.iloc[-1]
        last_ma50 = ma50.dropna().iloc[-1]
        last_ma200 = ma200.dropna().iloc[-1]

        signals = []
        if last_close > last_ma50:
            signals.append("price is **above** the 50-day MA (short-term bullish)")
        else:
            signals.append("price is **below** the 50-day MA (short-term bearish)")
        if last_close > last_ma200:
            signals.append("above the 200-day MA (long-term bullish)")
        else:
            signals.append("below the 200-day MA (long-term bearish)")
        if last_ma50 > last_ma200:
            signals.append("golden cross in effect (50-day > 200-day)")
        else:
            signals.append("death cross in effect (50-day < 200-day)")

        st.caption("Technical signals: " + " · ".join(signals) + ".")


# Trusted financial news sources (matched against provider.displayName and sourceId)
_TRUSTED_SOURCES = {
    "bloomberg", "reuters", "bbc", "new york times", "nytimes",
    "wall street journal", "wsj", "financial times", "ft.com",
    "cnbc", "marketwatch", "barron", "ap news", "associated press",
    "the economist", "economist", "forbes", "business insider",
    "ft", "seeking alpha", "morningstar", "investopedia",
}


def _is_trusted(provider: dict) -> bool:
    """Return True if the news provider is in the trusted-sources list."""
    name = (provider.get("displayName") or "").lower()
    source_id = (provider.get("sourceId") or "").lower()
    return any(t in name or t in source_id for t in _TRUSTED_SOURCES)


def _parse_news_item(item: dict) -> dict | None:
    """Normalise a yfinance 1.2+ news item (nested under 'content') into a flat dict.

    Returns None if the item lacks a title or URL.
    """
    content = item.get("content") or item  # fallback for older yfinance shapes
    title = content.get("title") or ""
    if not title:
        return None

    # Prefer clickThroughUrl (Yahoo Finance hosted link), fall back to canonicalUrl
    click = content.get("clickThroughUrl") or {}
    canonical = content.get("canonicalUrl") or {}
    link = click.get("url") or canonical.get("url") or content.get("link") or "#"

    provider = content.get("provider") or {}
    publisher = provider.get("displayName") or content.get("publisher") or ""

    pub_date = (
        content.get("pubDate")
        or content.get("displayTime")
        or content.get("providerPublishTime")  # older shape
    )

    return {
        "title": title,
        "link": link,
        "publisher": publisher,
        "pub_date": pub_date,
        "provider": provider,
    }


def _render_news(news: list[dict]):
    st.subheader("Recent News")

    if not news:
        st.info("No recent news available for this ticker.")
        return

    # Only show items from trusted outlets — no fallback to other sources
    parsed  = [p for item in news if (p := _parse_news_item(item))]
    trusted = [p for p in parsed if _is_trusted(p["provider"])][:5]

    if not trusted:
        st.info("No recent news from major financial outlets (Bloomberg, Reuters, WSJ, etc.) available for this ticker.")
        return

    for item in trusted:
        time_str = _time_ago(item["pub_date"])
        caption_parts = [p for p in [item["publisher"], time_str] if p]
        st.markdown(f"[{item['title']}]({item['link']})")
        if caption_parts:
            st.caption(" · ".join(caption_parts))
