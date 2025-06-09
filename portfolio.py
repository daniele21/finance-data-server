from collections import defaultdict
from datetime import datetime
import pandas as pd
import database
import data_fetcher


def get_portfolio_status(portfolio_name):
    """Return current holdings with latest prices."""
    txs = database.get_transactions(portfolio_name)
    positions = database.aggregate_positions(txs)
    holdings = []
    total_value = 0.0
    for ticker, qty in positions.items():
        if qty == 0:
            continue
        data, _ = data_fetcher.fetch_with_cache(ticker)
        info = data.get("info", {}) if data else {}
        price = info.get("regularMarketPrice", 0)
        value = price * qty
        total_value += value
        holdings.append({
            "ticker": ticker,
            "quantity": qty,
            "price": price,
            "value": value,
        })
    return {"holdings": holdings, "total_value": total_value}


def get_performance(portfolio_name):
    """Compute simple performance trend using daily closes."""
    txs = database.get_transactions(portfolio_name)
    if not txs:
        return []
    first_date = min(t["date"] for t in txs)
    positions = database.aggregate_positions(txs)
    history_dict = {}
    for ticker, qty in positions.items():
        if qty == 0:
            continue
        data, _ = data_fetcher.fetch_with_cache(ticker)
        hist = (data or {}).get("history", [])
        if not hist:
            continue
        df = pd.DataFrame(hist)
        if df.empty or "Date" not in df.columns or "Close" not in df.columns:
            continue
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df = df[df.index >= first_date]
        history_dict[ticker] = df["Close"]
    if not history_dict:
        return []
    df = pd.DataFrame(history_dict)
    df.sort_index(inplace=True)
    df.ffill(inplace=True)
    values = []
    for date, row in df.iterrows():
        total = 0.0
        for ticker, qty in positions.items():
            price = row.get(ticker, 0)
            total += price * qty
        values.append({"date": date.strftime("%Y-%m-%d"), "value": total})
    return values

