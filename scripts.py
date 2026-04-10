import mysql.connector
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine

from const import SESSION

db_connection_str = "mysql+mysqlconnector://root:8888@192.168.50.31:6608/FYP"
# Create the SQLAlchemy engine
engine = create_engine(db_connection_str)


# 1. Initialisation (all stocks from earliest transaction date to today)
# 2. New transaction with new stock -> from that transaction date to today
# 3. New transaction with existing stock with new earliest date -> new earliest date to prev earliest date
# 4. New updates (latest date to today)
# 5. Remove prices after exiting whole position

# eventID, symbol, date, eventType, amount

# eventType: 0 for stock split, 1 for dividend

# amount: 2.0 for 2-for-1 split, 0.5 for 1-for-2 split


# may call this function after new holdings are added
def get_events(ticker_list):
    tickers = yf.Tickers(" ".join(ticker_list))

    list_of_dfs = []
    # Loop through tickers to get calendar events
    for ticker in ticker_list:
        print(f"--- {ticker} Events ---")
        # Access dividend/split data
        try:
            df = tickers.tickers[ticker].actions
        except TypeError as e:
            print(e)
            continue
        df.index = df.index.date
        df["symbol"] = ticker
        df["date"] = df.index

        stock_splits = df.loc[df["Dividends"] == 0].copy()
        dividends = df.loc[df["Dividends"] != 0].copy()

        stock_splits.rename(columns={"Stock Splits": "amount"}, inplace=True)
        dividends.rename(columns={"Dividends": "amount"}, inplace=True)

        stock_splits["eventType"] = 0
        dividends["eventType"] = 1

        stock_splits = stock_splits[["symbol", "date", "eventType", "amount"]]
        dividends = dividends[["symbol", "date", "eventType", "amount"]]

        list_of_dfs.extend([stock_splits, dividends])
    df = pd.concat([d for d in list_of_dfs if not d.empty], ignore_index=True)
    print(df)

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

        df.to_sql(name="Stock_Event", con=engine, if_exists="append", index=False)
        engine.dispose()

    except mysql.connector.Error as err:
        print(f"Error: {err}")


def get_holdings(_conn, cache_key=None) -> pd.DataFrame:
    holdings_df = _conn.query(
        "SELECT h.symbol, h.quantity, h.costBasis, a.currentPrice FROM Holding h JOIN Asset a ON h.symbol = a.symbol",
        ttl=0,
    )
    holdings_df["weight"] = holdings_df["quantity"] * holdings_df["currentPrice"]
    holdings_df["weight"] = holdings_df["weight"] / holdings_df["weight"].sum()
    return holdings_df


if __name__ == "__main__":
    ticker = yf.Ticker("HSBA.L", session=SESSION)
    print(ticker.analyst_price_targets)
    # get_events(["VOO", "RDDT", "TSLA", "2628.HK", "SGOV", "GLD", "IBIT", "NVDA"])
