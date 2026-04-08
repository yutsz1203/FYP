import csv
import time
from datetime import date

import mariadb
import mysql.connector
import pandas as pd
import streamlit as st
import yfinance as yf
from dateutil.relativedelta import relativedelta
from sqlalchemy import create_engine
from tqdm import tqdm

from const import CLASS_MAP, CURRENCIES, SECTOR_MAP, SESSION

db_connection_str = "mysql+mysqlconnector://root:8888@192.168.50.31:6608/FYP"
engine = create_engine(db_connection_str)


def db_connect():
    cfg = st.secrets["mariadb"]
    try:
        conn = mariadb.connect(
            host=cfg["host"],
            port=cfg.get("port", 6608),
            user=cfg["user"],
            password=cfg["password"],
            database="FYP",
        )
        conn.autocommit = True
        return conn.cursor()
    except mariadb.Error as e:
        st.error(f"Connection error: {e}")
        return None


def insert_db(conn, ticker, price, sector, assetClass):
    try:
        conn.execute(
            "INSERT INTO Asset (symbol, currentPrice, sector, class) VALUES (?, ?, ?, ?)",
            (ticker, price, sector, assetClass),
        )
    except mariadb.Error as e:
        return update_db(conn, ticker, price)


def update_db(conn, ticker, price):
    try:
        conn.execute(
            "UPDATE Asset SET currentPrice = ? WHERE symbol = ?", (price, ticker)
        )
    except mariadb.Error as e:
        print(e)
        return None


def fetch_db(conn):
    try:
        conn.execute("SELECT symbol FROM Asset")
    except mariadb.Error as e:
        print(e)
        return None
    return conn.fetchall()


def Test():
    ticker = yf.Ticker("9999.HK")
    print(ticker.info)


def read_csv():
    result = []
    with open("us_symbols.csv", newline="") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=",")
        next(spamreader)
        for row in spamreader:
            result.append(row[0])
    return result


def Screener(conn):
    quotes = read_csv()
    for quote in quotes:
        info = yf.Ticker(quote, session=SESSION).info
        if "symbol" not in info:
            continue
        ticker = quote
        print(ticker)
        if "regularMarketPrice" in info:
            price = info["regularMarketPrice"]
        elif "regularMarketPreviousClose" in info:
            price = info["regularMarketPreviousClose"]
        else:
            continue
        sector = None
        assetClass = None
        if "sector" in info:
            sector = info["sector"]
            sector = SECTOR_MAP[sector]
        if "typeDisp" in info:
            assetClass = info["typeDisp"]
            assetClass = CLASS_MAP[assetClass]
        insert_db(conn, ticker, price, sector, assetClass)
    return None


def tickerFetch(quote, session):
    try:
        return yf.Ticker(quote, session=session).info
    except:
        time.sleep(5 * 60)
        return tickerFetch(quote, session)


def Updater(conn):
    # off = 0
    # q = yf.EquityQuery("eq", ["region", region])  # List[Str] -> List[QueryBase]
    # response = yf.screen(q, size=250, offset=off, session=SESSION, sortAsc=True)
    quotes = fetch_db(conn)
    if quotes is None:
        return 0
    for quote in tqdm(quotes):
        # print(quote["symbol"])
        # if len(quote["symbol"]) > 7:
        #     continue
        quote = quote[0]
        # print(quote)
        info = tickerFetch(quote, SESSION)
        ticker = quote
        if "regularMarketPrice" in info:
            price = info["regularMarketPrice"]
        elif "regularMarketPreviousClose" in info:
            price = info["regularMarketPreviousClose"]
        else:
            continue
        # insert_db(conn, ticker, price, SECTOR_MAP[sector], CLASS_MAP[assetClass])
        update_db(conn, ticker, price)
        # print(ticker, price, SECTOR_MAP[sector], assetClass)


def update_rates(currencies):
    try:
        connection = mysql.connector.connect(
            host="192.168.50.31",
            port=6608,
            user="root",
            passwd="8888",
            database="FYP",
        )
        if connection.is_connected():
            print("Successfully connected to MySQL database.")

        cursor = connection.cursor()
        dfs = []
        for currency_ticker, currency in currencies:
            print(f"Processing {currency}...")
            cursor.execute(
                f"SELECT date FROM Rate WHERE currency = '{currency}' ORDER BY date DESC LIMIT 1"
            )
            results = cursor.fetchone()
            if results:
                start = results[0] - relativedelta(days=2)
                rates = yf.download(
                    currency_ticker, start=start, end=date.today(), interval="1d"
                )
            else:
                rates = yf.download(currency_ticker, period="10y", interval="1d")
                start = rates.index.min().date()

            if not rates.empty:
                df = rates["Close"].copy()
                df.columns = ["rate"]
                df = df.reindex(pd.date_range(start=start, end=date.today(), freq="D"))
                df["rate"] = df["rate"].ffill()
                df["currency"] = currency
                df["date"] = df.index
                df = df[df["date"].dt.date > start + relativedelta(days=2)]
                dfs.append(df)
            else:
                print(f"Rates ({currency}) up to date.")
        final = pd.concat(dfs, ignore_index=True)
        final.to_sql(name="Rate", con=engine, if_exists="append", index=False)
        engine.dispose()

    except mysql.connector.Error as err:
        print(f"Error: {err}")


if __name__ == "__main__":
    # read_csv()
    conn = db_connect()
    # print(conn)
    # Test()
    # Screener(conn)
    Updater(conn)

    update_rates(CURRENCIES)
