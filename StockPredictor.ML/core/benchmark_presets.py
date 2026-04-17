from __future__ import annotations


TICKER_BASKETS = {
    "starter": ["AAPL", "TSLA", "DOU.DE"],
    "bachelor_core": ["AAPL", "MSFT", "NVDA", "TSLA", "JPM", "XOM", "KO", "SAP.DE"],
    "bachelor_diversified": [
        "AAPL",
        "MSFT",
        "NVDA",
        "TSLA",
        "JPM",
        "XOM",
        "KO",
        "PG",
        "SAP.DE",
        "DTE.DE",
    ],
}


def get_ticker_basket(name: str) -> list[str]:
    if name not in TICKER_BASKETS:
        raise ValueError(
            f"Unknown basket preset '{name}'. Expected one of: {', '.join(TICKER_BASKETS)}."
        )

    return list(TICKER_BASKETS[name])


def list_ticker_basket_names() -> list[str]:
    return list(TICKER_BASKETS)
