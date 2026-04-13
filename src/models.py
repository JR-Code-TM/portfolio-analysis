from __future__ import annotations

from typing import Optional, TypedDict


class _HoldingRequired(TypedDict):
    ticker: str
    company_name: str
    sector: str
    shares: float


class Holding(_HoldingRequired, total=False):
    price: Optional[float]       # None = auto-fetch attempted; still None if yfinance failed
    cost_basis: Optional[float]  # None = skip gain/loss calculations
    country: Optional[str]
    is_etf: bool


SECTORS = [
    "Technology",
    "Healthcare",
    "Financials",
    "Consumer Discretionary",
    "Communication Services",
    "Industrials",
    "Consumer Staples",
    "Energy",
    "Utilities",
    "Real Estate",
    "Materials",
    "Other",
]
