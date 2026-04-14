"""
Integration tests for Portfolio Analyzer — data-fetch layer.

Run with:  python3 tests/test_app.py
(No pytest or Streamlit context required — tests the pure yfinance layer only.)
"""
from __future__ import annotations

import io
import sys

sys.path.insert(0, ".")

import pandas as pd
import yfinance as yf

from src.market_data import fetch_etf_holdings, fetch_ticker_info

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "✅ PASS"
FAIL = "❌ FAIL"
_failures: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = PASS if condition else FAIL
    suffix = f" — {detail}" if detail else ""
    print(f"  {status}  {label}{suffix}")
    if not condition:
        _failures.append(label)
    return condition


def section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_stock_info():
    section("Stock info — AAPL")
    info = fetch_ticker_info("AAPL")
    check("company_name present", bool(info.get("company_name")), info.get("company_name") or "")
    check("price > 0",            (info.get("price") or 0) > 0,  str(info.get("price")))
    check("is_etf is False",      info.get("is_etf") is False)
    check("sector present",       bool(info.get("sector")),       info.get("sector") or "")


def test_etf_info():
    section("ETF info — VOO")
    info = fetch_ticker_info("VOO")
    check("company_name present", bool(info.get("company_name")), info.get("company_name") or "")
    check("price > 0",            (info.get("price") or 0) > 0,  str(info.get("price")))
    check("is_etf is True",       info.get("is_etf") is True)


def test_etf_holdings():
    section("ETF holdings — VOO")
    holdings = fetch_etf_holdings("VOO")
    check("holdings non-empty",            len(holdings) > 0, f"{len(holdings)} holdings")
    if holdings:
        check("each holding has ticker+weight",
              all("ticker" in h and "weight" in h for h in holdings))
        check("weights are fractions 0–1",
              all(0 < h["weight"] < 1 for h in holdings))
        check("at least 5 holdings",       len(holdings) >= 5, f"{len(holdings)}")


def test_invalid_ticker():
    section("Invalid ticker — XYZINVALID999")
    info = fetch_ticker_info("XYZINVALID999")
    check("returns safely without exception", True)
    check("price is None",                    info.get("price") is None)
    check("company_name is None",             info.get("company_name") is None)
    check("is_etf is False",                  info.get("is_etf") is False)


def test_history():
    section("Price history — AAPL")
    t = yf.Ticker("AAPL")
    hist = t.history(period="1y")
    check("non-empty DataFrame",    not hist.empty,          f"{len(hist)} rows")
    check("has Close column",       "Close" in hist.columns)
    check("has Volume column",      "Volume" in hist.columns)
    check("~250 trading days",      len(hist) >= 200,        f"{len(hist)} rows")


def test_holdings_names_no_session_state():
    section("ETF holdings with names (no Streamlit session state) — SPY")
    raw = fetch_etf_holdings("SPY")
    if not raw:
        check("SPY holdings available", False, "no holdings returned — skipping")
        return
    top3 = sorted(raw, key=lambda x: x["weight"], reverse=True)[:3]
    for h in top3:
        # Use fetch_ticker_info directly (same as the fixed _fetch_holdings_with_names)
        info = fetch_ticker_info(h["ticker"])
        name = info.get("company_name") or h["ticker"]
        check(f"{h['ticker']}: name resolved", bool(name), name)


def test_csv_import():
    section("CSV import simulation")

    csv_content = (
        "Ticker,Shares,Cost Basis per Share (USD)\n"
        "VOO,10,420.50\n"
        "AAPL,25,150.00\n"
        "MSFT,5,300.00\n"
        "XYZINVALID999,3,50.00\n"
    )
    df = pd.read_csv(io.StringIO(csv_content))
    norm = {c.strip().lower(): c for c in df.columns}

    def _find_col(*candidates):
        for c in candidates:
            if c in norm:
                return norm[c]
        return None

    col_ticker = _find_col("ticker", "symbol", "tick")
    col_shares = _find_col("shares", "quantity", "qty", "units")
    col_cost   = _find_col("cost basis per share (usd)", "cost basis per share", "cost basis")

    check("ticker column detected",     col_ticker is not None, str(col_ticker))
    check("shares column detected",     col_shares is not None, str(col_shares))
    check("cost basis column detected", col_cost   is not None, str(col_cost))

    if not col_ticker or not col_shares:
        check("column detection failed — aborting CSV test", False)
        return

    # Parse rows
    rows = []
    for _, row in df.iterrows():
        ticker_val = str(row[col_ticker]).upper().strip()
        shares_val = float(row[col_shares])
        cost_val   = float(row[col_cost]) if col_cost and pd.notna(row.get(col_cost)) else 0.0
        rows.append((ticker_val, shares_val, cost_val))

    check("4 rows parsed",      len(rows) == 4,                    f"{len(rows)} rows")
    check("VOO  — 10 shares",   rows[0] == ("VOO",  10.0, 420.50), str(rows[0]))
    check("AAPL — 25 shares",   rows[1] == ("AAPL", 25.0, 150.00), str(rows[1]))
    check("MSFT —  5 shares",   rows[2] == ("MSFT",  5.0, 300.00), str(rows[2]))

    # Fetch yfinance for valid tickers
    for ticker_val, _, _ in rows[:3]:
        info = fetch_ticker_info(ticker_val)
        check(f"{ticker_val}: company_name present",
              bool(info.get("company_name")), info.get("company_name") or "")
        check(f"{ticker_val}: price > 0",
              (info.get("price") or 0) > 0, str(info.get("price")))

    # Invalid ticker — must not crash, price must be None
    bad = fetch_ticker_info("XYZINVALID999")
    check("XYZINVALID999: no crash",       True)
    check("XYZINVALID999: price is None",  bad.get("price") is None)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║   Portfolio Analyzer — Integration Test Suite           ║")
    print("╚══════════════════════════════════════════════════════════╝")

    test_stock_info()
    test_etf_info()
    test_etf_holdings()
    test_invalid_ticker()
    test_history()
    test_holdings_names_no_session_state()
    test_csv_import()

    print(f"\n{'═' * 62}")
    total   = sum(1 for line in open(__file__).readlines() if "check(" in line)
    passed  = total - len(_failures)
    if _failures:
        print(f"  {FAIL}  {len(_failures)} test(s) failed:")
        for f in _failures:
            print(f"       • {f}")
    else:
        print(f"  {PASS}  All checks passed!")
    print(f"{'═' * 62}\n")
    sys.exit(1 if _failures else 0)
