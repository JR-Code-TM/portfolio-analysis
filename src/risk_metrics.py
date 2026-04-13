from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from src.market_data import (
    fetch_price_history,
    fetch_benchmark,
    get_etf_holdings_cached,
    expand_holdings_for_analysis,
)

RISK_FREE_RATE_ANNUAL = 0.05
TRADING_DAYS = 252


def render_metrics(holdings: list[dict]):
    if not holdings:
        st.info("No holdings yet. Add holdings using the sidebar.")
        return

    # Collect base tickers + ETF sub-tickers for one combined price fetch
    base_tickers = list({h["ticker"] for h in holdings})
    sub_tickers = [
        sub["ticker"]
        for h in holdings if h.get("is_etf", False)
        for sub in get_etf_holdings_cached(h["ticker"])
    ]
    all_tickers = tuple(set(base_tickers + sub_tickers))

    with st.spinner("Computing risk metrics…"):
        price_data, synthetic_tickers = fetch_price_history(all_tickers)
        benchmark = fetch_benchmark()

    # Expand ETF holdings into virtual sub-holdings for analysis
    expanded = expand_holdings_for_analysis(holdings, price_data)

    # Only warn about synthetic data for user-visible base tickers
    user_synthetic = [t for t in synthetic_tickers if t in base_tickers]
    if user_synthetic:
        st.warning(
            f"Metrics estimated from simulated price data for: {', '.join(user_synthetic)}"
        )

    portfolio_returns, bench_returns = _compute_returns(expanded, price_data, benchmark)

    if portfolio_returns is None or len(portfolio_returns) < 20:
        st.error("Not enough return data to compute risk metrics.")
        return

    sharpe = _sharpe_ratio(portfolio_returns)
    sortino = _sortino_ratio(portfolio_returns)
    max_dd = _max_drawdown(portfolio_returns)
    beta, alpha = _beta_alpha(portfolio_returns, bench_returns)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "Sharpe Ratio",
        f"{sharpe:.2f}",
        help="Risk-adjusted return: (portfolio return − risk-free rate) / volatility. Higher is better. >1 is good.",
    )
    c2.metric(
        "Sortino Ratio",
        f"{sortino:.2f}",
        help="Like Sharpe but only penalises downside volatility. Higher is better.",
    )
    c3.metric(
        "Max Drawdown",
        f"{max_dd:.2f}%",
        help="Largest peak-to-trough decline. More negative is worse.",
    )
    c4.metric(
        "Beta",
        f"{beta:.2f}",
        help="Sensitivity to S&P 500 movements. Beta=1 moves with market; >1 is more volatile.",
    )
    c5.metric(
        "Alpha",
        f"{alpha:.2f}%",
        help="Annualised excess return above what beta-adjusted market exposure would predict (Jensen's Alpha).",
    )

    st.divider()
    _render_return_stats(portfolio_returns, bench_returns)


def _compute_returns(
    holdings: list[dict],
    price_data: dict[str, pd.Series],
    benchmark: pd.Series,
) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    all_dates = benchmark.index
    for series in price_data.values():
        all_dates = all_dates.union(series.index)
    all_dates = all_dates.sort_values()

    aligned = {
        ticker: series.reindex(all_dates).ffill().bfill()
        for ticker, series in price_data.items()
    }
    bench_aligned = benchmark.reindex(all_dates).ffill().bfill()

    portfolio_value = pd.Series(0.0, index=all_dates)
    for h in holdings:
        ticker = h["ticker"]
        price = h.get("price")
        if ticker in aligned:
            portfolio_value += h["shares"] * aligned[ticker]
        elif price is not None:
            # Holding has no price history — use constant price (contributes 0 to returns)
            portfolio_value += h["shares"] * price

    portfolio_returns = portfolio_value.pct_change().dropna()
    bench_returns = bench_aligned.pct_change().dropna()

    # Remove inf / extreme values from returns
    portfolio_returns = portfolio_returns.replace([np.inf, -np.inf], np.nan).dropna()
    bench_returns = bench_returns.replace([np.inf, -np.inf], np.nan).dropna()

    common = portfolio_returns.index.intersection(bench_returns.index)
    if len(common) < 20:
        return None, None
    return portfolio_returns.loc[common], bench_returns.loc[common]


def _sharpe_ratio(returns: pd.Series) -> float:
    rf_daily = RISK_FREE_RATE_ANNUAL / TRADING_DAYS
    excess = returns - rf_daily
    if returns.std() == 0:
        return 0.0
    return float(excess.mean() / returns.std() * np.sqrt(TRADING_DAYS))


def _sortino_ratio(returns: pd.Series) -> float:
    rf_daily = RISK_FREE_RATE_ANNUAL / TRADING_DAYS
    excess = returns - rf_daily
    downside = returns[returns < 0]
    if len(downside) == 0 or downside.std() == 0:
        return 0.0
    return float(excess.mean() / downside.std() * np.sqrt(TRADING_DAYS))


def _max_drawdown(returns: pd.Series) -> float:
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min() * 100)


def _beta_alpha(portfolio_returns: pd.Series, bench_returns: pd.Series) -> tuple[float, float]:
    cov_matrix = np.cov(portfolio_returns, bench_returns)
    bench_var = cov_matrix[1, 1]
    if bench_var == 0:
        return 1.0, 0.0

    beta = float(cov_matrix[0, 1] / bench_var)
    port_annual = float((1 + portfolio_returns.mean()) ** TRADING_DAYS - 1)
    bench_annual = float((1 + bench_returns.mean()) ** TRADING_DAYS - 1)
    alpha = (port_annual - (RISK_FREE_RATE_ANNUAL + beta * (bench_annual - RISK_FREE_RATE_ANNUAL))) * 100

    return beta, float(alpha)


def _render_return_stats(portfolio_returns: pd.Series, bench_returns: pd.Series):
    st.subheader("Return Statistics")

    port_annual = (1 + portfolio_returns.mean()) ** TRADING_DAYS - 1
    bench_annual = (1 + bench_returns.mean()) ** TRADING_DAYS - 1
    port_vol = portfolio_returns.std() * np.sqrt(TRADING_DAYS)
    bench_vol = bench_returns.std() * np.sqrt(TRADING_DAYS)

    stats = pd.DataFrame({
        "Metric": [
            "Annualised Return",
            "Annualised Volatility",
            "Daily Return (avg)",
            "Best Day",
            "Worst Day",
            "Positive Days",
        ],
        "Portfolio": [
            f"{port_annual * 100:.2f}%",
            f"{port_vol * 100:.2f}%",
            f"{portfolio_returns.mean() * 100:.3f}%",
            f"{portfolio_returns.max() * 100:.2f}%",
            f"{portfolio_returns.min() * 100:.2f}%",
            f"{(portfolio_returns > 0).mean() * 100:.1f}%",
        ],
        "S&P 500": [
            f"{bench_annual * 100:.2f}%",
            f"{bench_vol * 100:.2f}%",
            f"{bench_returns.mean() * 100:.3f}%",
            f"{bench_returns.max() * 100:.2f}%",
            f"{bench_returns.min() * 100:.2f}%",
            f"{(bench_returns > 0).mean() * 100:.1f}%",
        ],
    })

    st.dataframe(stats, use_container_width=True, hide_index=True)
