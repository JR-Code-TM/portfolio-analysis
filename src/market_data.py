import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=300, show_spinner="Fetching market data...")
def fetch_price_history(tickers: list[str], period: str = "1y") -> tuple[dict[str, pd.Series], list[str]]:
    """Fetch historical closing prices for a list of tickers.

    Returns (price_dict, synthetic_tickers) where synthetic_tickers lists
    tickers that fell back to simulated data.
    """
    prices = {}
    synthetic = []

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


def update_current_prices(holdings: list[dict]) -> list[dict]:
    """Update holdings with latest prices from yfinance."""
    tickers = list({h["ticker"] for h in holdings})
    updated_prices = {}

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.get("lastPrice") or info.get("last_price")
            if price and price > 0:
                updated_prices[ticker] = float(price)
        except Exception:
            pass

    for h in holdings:
        if h["ticker"] in updated_prices:
            h["price"] = updated_prices[h["ticker"]]

    return holdings
