from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


# ---------------------------------------------------------------------------
# Price history
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300, show_spinner="Fetching market data...")
def fetch_price_history(tickers: tuple, period: str = "1y") -> tuple:
    """Fetch historical closing prices for a list of tickers.

    Returns (price_dict, synthetic_tickers) where synthetic_tickers lists
    tickers that fell back to simulated data.

    Note: takes a tuple (not list) so it is hashable for @st.cache_data.
    """
    prices: dict[str, pd.Series] = {}
    synthetic: list[str] = []

    for ticker in tickers:
        try:
            data = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if data.empty or len(data) < 10:
                raise ValueError("Insufficient data")
            close = data["Close"]
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            prices[ticker] = close.dropna()
        except Exception:
            prices[ticker] = _generate_synthetic(ticker, period)
            synthetic.append(ticker)

    return prices, synthetic


@st.cache_data(ttl=300, show_spinner="Fetching S&P 500 data...")
def fetch_benchmark(period: str = "1y") -> pd.Series:
    """Fetch S&P 500 index historical prices."""
    try:
        data = yf.download("^GSPC", period=period, progress=False, auto_adjust=True)
        if data.empty:
            raise ValueError("No benchmark data")
        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return close.dropna()
    except Exception:
        return _generate_synthetic("SP500_BENCH", period)


def _generate_synthetic(ticker: str, period: str = "1y") -> pd.Series:
    """Generate synthetic price data using geometric Brownian motion."""
    period_days = {"1mo": 21, "3mo": 63, "6mo": 126, "1y": 252, "2y": 504, "5y": 1260}
    days = period_days.get(period, 252)

    rng = np.random.default_rng(seed=hash(ticker) % (2**31))
    mu = 0.08 / 252
    sigma = 0.25 / np.sqrt(252)
    start_price = 100.0 + rng.random() * 200

    returns = rng.normal(mu, sigma, days)
    prices = start_price * np.exp(np.cumsum(returns))

    end_date = pd.Timestamp.today().normalize()
    dates = pd.bdate_range(end=end_date, periods=days)
    return pd.Series(prices, index=dates, name=ticker)


# ---------------------------------------------------------------------------
# Ticker info lookup (company name, sector, country, price, is_etf)
# ---------------------------------------------------------------------------

def fetch_ticker_info(ticker: str) -> dict:
    """Fetch company info from yfinance with three-tier fallback.

    Tier 1 — .info: most complete but can be throttled on cloud IPs.
    Tier 2 — fast_info: lighter endpoint, more resilient to rate-limits.
    Tier 3 — yf.download: different Yahoo endpoint, last resort for price.

    Each tier runs in its own try/except so a failure in Tier 1 never
    prevents Tier 2 or 3 from being attempted.
    """
    info: dict = {}
    price = None
    company_name = None
    is_etf = False
    t = yf.Ticker(ticker)

    # Tier 1: full .info dict
    try:
        info = t.info or {}
        is_etf = info.get("quoteType", "").upper() == "ETF"
        company_name = info.get("longName") or info.get("shortName")
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("navPrice")
        )
    except Exception:
        pass

    # Tier 2: fast_info — lighter, survives cloud throttling
    if price is None:
        try:
            fi = t.fast_info
            price = getattr(fi, "last_price", None) or getattr(fi, "lastPrice", None)
        except Exception:
            pass

    # Tier 3: yf.download — different Yahoo endpoint, last resort
    if price is None:
        try:
            hist = yf.download(ticker, period="5d", progress=False, auto_adjust=True)
            if not hist.empty:
                close = hist["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                last = close.dropna()
                if not last.empty:
                    price = float(last.iloc[-1])
        except Exception:
            pass

    # If price resolved but name still missing, ticker symbol is a valid fallback
    # (a resolvable price proves the ticker exists)
    if not company_name and price:
        company_name = ticker

    return {
        "company_name": company_name,
        "sector": info.get("sector"),
        "country": info.get("country"),
        "price": float(price) if price else None,
        "is_etf": is_etf,
    }


def get_ticker_info_cached(ticker: str) -> dict:
    """Return cached ticker info, fetching if not yet cached."""
    cache = st.session_state.setdefault("ticker_info_cache", {})
    if ticker not in cache:
        cache[ticker] = fetch_ticker_info(ticker)
    return cache[ticker]


def get_country_cached(ticker: str) -> Optional[str]:
    """Return country for a ticker, using/populating the ticker_info_cache."""
    info = get_ticker_info_cached(ticker)
    return info.get("country")


# ---------------------------------------------------------------------------
# ETF holdings
# ---------------------------------------------------------------------------

def fetch_etf_holdings(etf_ticker: str) -> list[dict]:
    """Return top holdings of an ETF as [{"ticker": str, "weight": float}].

    Weights are fractions (0.0–1.0). Returns [] on any failure.
    Requires yfinance >= 0.2.37 for funds_data.top_holdings.
    """
    try:
        t = yf.Ticker(etf_ticker)
        top = t.funds_data.top_holdings
        if top is None or (hasattr(top, "empty") and top.empty):
            return []
        records = []
        for sym, row in top.iterrows():
            weight = float(row.get("Holding Percent", row.get("holdingPercent", 0.0)))
            if weight > 0 and str(sym).upper() not in ("NAN", "NONE", ""):
                records.append({"ticker": str(sym).upper(), "weight": weight})
        return records
    except Exception:
        return []


def get_etf_holdings_cached(etf_ticker: str) -> list[dict]:
    """Return cached ETF holdings, fetching if not yet cached."""
    cache = st.session_state.setdefault("etf_holdings_cache", {})
    if etf_ticker not in cache:
        cache[etf_ticker] = fetch_etf_holdings(etf_ticker)
    return cache[etf_ticker]


# ---------------------------------------------------------------------------
# ETF expansion helper
# ---------------------------------------------------------------------------

def expand_holdings_for_analysis(
    holdings: list[dict],
    price_data: dict[str, pd.Series],
) -> list[dict]:
    """Replace ETF holdings with their underlying constituents for analysis.

    For each ETF holding:
    - Fetch top holdings with weights from cache
    - Compute virtual_shares = (etf_market_value * weight) / sub_price
    - Attach sector and country from ticker_info_cache where available
    - Falls back to the original ETF holding if decomposition fails

    Non-ETF holdings are returned unchanged.
    """
    expanded: list[dict] = []

    for h in holdings:
        if not h.get("is_etf", False):
            # Ensure non-ETF holding has country populated if possible
            if not h.get("country"):
                h = dict(h)
                h["country"] = get_country_cached(h["ticker"])
            expanded.append(h)
            continue

        # Compute ETF market value
        etf_price = h.get("price")
        if etf_price is None and h["ticker"] in price_data:
            etf_price = float(price_data[h["ticker"]].iloc[-1])
        if etf_price is None:
            expanded.append(h)
            continue

        etf_mv = h["shares"] * etf_price
        sub_holdings = get_etf_holdings_cached(h["ticker"])

        if not sub_holdings:
            # Fallback: keep ETF as-is
            expanded.append(h)
            continue

        decomposed_any = False
        for sub in sub_holdings:
            sub_t = sub["ticker"]
            weight = sub["weight"]

            # Get sub-holding price from price_data (last available close)
            if sub_t not in price_data:
                continue
            sub_price = float(price_data[sub_t].iloc[-1])
            if sub_price <= 0:
                continue

            virtual_shares = (etf_mv * weight) / sub_price

            # Get sector and country — fetch from yfinance if not yet cached
            sub_info = get_ticker_info_cached(sub_t)
            sub_sector = sub_info.get("sector") or "Other"
            sub_country = sub_info.get("country")
            sub_name = sub_info.get("company_name") or sub_t

            expanded.append({
                "ticker": sub_t,
                "company_name": sub_name,
                "sector": sub_sector,
                "shares": virtual_shares,
                "price": sub_price,
                "cost_basis": None,
                "country": sub_country,
                "is_etf": False,
            })
            decomposed_any = True

        if not decomposed_any:
            expanded.append(h)

    return expanded


# ---------------------------------------------------------------------------
# Current price refresh
# ---------------------------------------------------------------------------

def update_current_prices(holdings: list[dict]) -> list[dict]:
    """Refresh price fields using yfinance latest close."""
    tickers = list({h["ticker"] for h in holdings})
    updated_prices: dict[str, float] = {}

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            price = getattr(info, "last_price", None) or getattr(info, "lastPrice", None)
            if price and price > 0:
                updated_prices[ticker] = float(price)
        except Exception:
            pass

    for h in holdings:
        if h["ticker"] in updated_prices:
            h["price"] = updated_prices[h["ticker"]]

    return holdings
