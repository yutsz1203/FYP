import yfinance as yf
import mariadb
import streamlit as st
from curl_cffi import requests
import csv
from tqdm import tqdm
import time

SESSION = requests.Session(impersonate="chrome")
HK_MAX = 9999
US_MAX = 19161
SECTOR_MAP = {
    "Healthcare": 1,
    "Financial Services": 2,
    "Technology": 3,
    "Industrials": 4,
    "Consumer Cyclical": 5,
    "Basic Materials": 6,
    "Communication Services": 7,
    "Real Estate": 8,
    "Energy": 9,
    "Consumer Defensive": 10,
    "Utilities": 11,
    "": 0,
}

CLASS_MAP = {
    "Equity": 1,
    "Bond": 2,
    "Commodity": 3,
    "Cryptocurrency": 4,
    "ETF": 5,
    "Fund": 6,
}


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


# read_csv()
conn = db_connect()
# print(conn)
# Test()
# Screener(conn)
Updater(conn)
