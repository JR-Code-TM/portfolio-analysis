from typing import TypedDict


class Holding(TypedDict):
    ticker: str
    company_name: str
    sector: str
    shares: float
    price: float
    cost_basis: float


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
