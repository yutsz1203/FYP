import time

import streamlit as st
import yfinance as yf

now = time.localtime()
today = time.strftime("%Y-%m-%d")
periods = ["1W", "MTD", "1M", "3M", "YTD", "1Y", "All"]


@st.cache_data
def fetchData(tickers):
    data = yf.download(tickers, start="2025-01-01", end=today, auto_adjust=True)
    print("Fetched")
    return data["Close"]


def calcReturns(df):
    return df.pct_change(fill_method=None).dropna()


def calcWeightedReturns(returns, weights):
    portfolio = None
    tickers = returns.columns
    for i, t in enumerate(tickers):
        if i == 0:
            portfolio = returns[t] * weights[i]
        else:
            portfolio += returns[t] * weights[i]
    return portfolio


def cumulativeValue(prices):
    cumulative_returns_pct = (
        1 + prices.pct_change(fill_method=None).dropna()
    ).cumprod() - 1
    cumulative_returns_pct.iloc[0] = 0

    initial_investment = 10000
    return round(initial_investment * (1 + cumulative_returns_pct), 2)


def cumulativeReturn(returns):
    cumulative_returns = returns.cumsum()
    cumulative_returns.iloc[0] = 0
    cumulative_returns = round(cumulative_returns * 100, 2)
    df = cumulative_returns.reset_index()
    df.columns = ["Date", "Returns"]
    return df
