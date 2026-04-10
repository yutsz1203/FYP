import mariadb
import pandas as pd
import streamlit as st
import yfinance as yf

from const import CLASS_MAP, SECTOR_MAP, SESSION
from update_db import get_events, insert_db

from .db import fetch_holdings, fetch_stock_event


def get_tx(_conn):
    df = _conn.query(
        "SELECT * FROM FYP.Transaction",
    )
    df.drop(columns=["UID"], inplace=True)
    df.columns = [
        "TId",
        "Date",
        "Symbol",
        "Price",
        "Quantity",
        "Action",
        "Commission",
    ]
    lastid = df.iloc[-1]["TId"]
    st.session_state["lastrowid"] = lastid + 1
    return df


def insert_tx(form, conn):
    try:
        conn.execute(
            "INSERT INTO FYP.Transaction VALUES (?, ?, ?, ?, ?, ?, ?, ?)", form
        )
        holdings_df = fetch_holdings()
        tx_date, symbol, price, quantity, action, commission = form[1:-1]
        action = 1 - 2 * action  # buy -> 0 to 1, sell -> 1 to -1

        stock_events = fetch_stock_event()
        if symbol not in stock_events["symbol"].values:
            stock_events = get_events(conn, [symbol])

        quantity, price = normalize_historical_transaction(
            stock_events, symbol, tx_date, quantity, price
        )

        if symbol in holdings_df["Symbol"].values:
            new_quantity = holdings_df.loc[
                holdings_df["Symbol"] == symbol, "Position"
            ].item() + (action * quantity)
            new_costbasis = (
                holdings_df.loc[holdings_df["Symbol"] == symbol, "Cost Basis"].item()
                + (action * quantity * price)
                + (action * commission)
            )
            conn.execute(
                """
                UPDATE FYP.Holding
                SET quantity=?, costBasis=?
                WHERE symbol=?
                """,
                (new_quantity, new_costbasis, symbol),
            )

        else:
            insert_new_asset(conn, symbol)
            new_holding = (
                symbol,
                quantity * action,
                quantity * price * action + commission,
                1,
            )
            conn.execute("INSERT INTO FYP.Holding VALUES (?, ?, ?, ?)", new_holding)

        return 1
    except mariadb.Error as e:
        st.error(e)
        return 0


def insert_new_asset(conn, symbol: str):

    try:
        conn.execute("SELECT * FROM Asset WHERE symbol = ?", [symbol])
    except mariadb.Error as e:
        print(e)
        return None

    res = conn.fetchall()

    # Asset in Asset table already
    if res:
        print(f"{symbol} in Asset table already.")
        return

    ticker = yf.Ticker(symbol, session=SESSION)
    info = ticker.info

    if "regularMarketPrice" in info:
        price = info["regularMarketPrice"]
    elif "regularMarketPreviousClose" in info:
        price = info["regularMarketPreviousClose"]
    else:
        price = 0

    assetClass = info.get("typeDisp", "")
    if assetClass == "ETF":
        fund_data = ticker.funds_data
        sector_weightings = fund_data.sector_weightings

        # Sector 13: Multi (has sector weightings data)
        sector = 13 if sector_weightings else 12

        category = info.get("category", "")
        cleaned_category = category.strip().lower()
        bond_position = fund_data.asset_classes.get("bondPosition", 0)

        if not bond_position:
            bond_position = 0

        if "bond" in cleaned_category or bond_position > 0.8:
            assetClass = CLASS_MAP["Bond"]
        elif cleaned_category == "digital assets":
            assetClass = CLASS_MAP["Cryptocurrency"]
        elif "commodities" in cleaned_category or "commodity" in cleaned_category:
            assetClass = CLASS_MAP["Commodity"]
        else:
            assetClass = CLASS_MAP["Equity"]

    else:
        assetClass = CLASS_MAP[assetClass]
        sector = info.get("sector", "")
        sector = SECTOR_MAP[sector]

    insert_db(conn, symbol, price, sector, assetClass)

    print(
        f"Inserted {symbol}. Price: {price}; Sector: {sector}; Asset Class: {assetClass}."
    )


def normalize_historical_transaction(stock_events, ticker, tx_date, tx_qty, tx_price):
    """
    Converts historical units to current units based on split history.
    """
    cumulative_factor = 1.0
    stock_events = stock_events[
        (stock_events["symbol"] == ticker) & (stock_events["date"] > tx_date)
    ]
    if not stock_events.empty:
        cumulative_factor *= stock_events["amount"].prod()

    normalized_qty = tx_qty * cumulative_factor
    normalized_price = tx_price / cumulative_factor

    return normalized_qty, normalized_price
