from datetime import date

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

from const import SECTOR_CASE_MAP
from src.fx import assign_currency, convert_to_base, get_rates_pivot

from .db import (
    fetch_holdings,
    fetch_price,
    fetch_rate,
    fetch_stock_event,
    fetch_transaction,
)

rate_df = fetch_rate()
rates_pivot = get_rates_pivot(rate_df)


def get_portfolio_value(
    assets, start, base_currency="USD", adjust=False
) -> pd.DataFrame:
    daily_holding_df = build_daily_holding()
    price_df = fetch_price(assets, start, adjust)
    tx_df = fetch_transaction()

    daily_holding_df["value_after_tx"] = (
        daily_holding_df["quantity"] * price_df["close"]
    )
    daily_holding_df.reset_index()
    daily_holding_df["prev_quantity"] = daily_holding_df.groupby("symbol")[
        "quantity"
    ].shift(1)
    tx_pairs = tx_df[["date", "symbol"]].drop_duplicates()
    tx_holdings = daily_holding_df.merge(tx_pairs, on=["date", "symbol"], how="inner")
    tx_holdings = tx_holdings.set_index(["date", "symbol"])
    tx_holdings["value_before_tx"] = tx_holdings["prev_quantity"] * price_df["close"]
    tx_holdings = tx_holdings.reset_index()

    daily_holding_df = daily_holding_df.merge(
        tx_holdings[["date", "symbol", "value_before_tx"]],
        on=["date", "symbol"],
        how="left",
    )
    daily_holding_df["value_before_tx"] = daily_holding_df["value_before_tx"].fillna(
        daily_holding_df["value_after_tx"]
    )
    first_tx_mask = (
        daily_holding_df["symbol"].isin(tx_pairs["symbol"])
        & daily_holding_df["prev_quantity"].isna()
    )
    daily_holding_df.loc[first_tx_mask, "value_before_tx"] = 0

    daily_holding_df = (
        daily_holding_df.groupby(["date", "currency"])
        .agg(
            value_after_tx=("value_after_tx", "sum"),
            value_before_tx=("value_before_tx", "sum"),
        )
        .reset_index()
    )

    daily_holding_df.loc[
        daily_holding_df["currency"] == "GBP", ["value_after_tx", "value_before_tx"]
    ] /= 100  # Adjust for pence

    daily_holding_df["base_value_after_tx"] = convert_to_base(
        df=daily_holding_df,
        value_col="value_after_tx",
        currency_col="currency",
        date_col="date",
        base_currency=base_currency,
        rates_pivot=rates_pivot,
    )

    daily_holding_df["base_value_before_tx"] = convert_to_base(
        df=daily_holding_df,
        value_col="value_before_tx",
        currency_col="currency",
        date_col="date",
        base_currency=base_currency,
        rates_pivot=rates_pivot,
    )

    daily_holding_df = daily_holding_df.round(2)
    daily_holding_df.dropna()  # this line should be removed after having a better fetch price logic
    daily_holding_df = daily_holding_df[
        daily_holding_df["base_value_after_tx"] > 0
    ]  # this line should be removed after having a better fetch price logic
    portfolio_value_df = daily_holding_df.groupby(["date"]).agg(
        base_value_after_tx=("base_value_after_tx", "sum"),
        base_value_before_tx=("base_value_before_tx", "sum"),
    )

    return portfolio_value_df


def get_holdings(base_currency: str = "USD") -> pd.DataFrame:
    """
    Build holdings df with adjustment to the base_currency.

    Parameters:
        base_currency: str

    Returns:
        holdings_df: Symbol, Current Price, Position, Market Value, Cost Basis, Unrealised P&L, Sector, Class, currency, pence_adjusted
    """
    holdings_df = fetch_holdings()
    holdings_df = assign_currency(holdings_df, "Symbol")
    holdings_df.loc[
        holdings_df["currency"] == "GBP", "Cost Basis"
    ] /= 100  # Adjust for pence
    holdings_df["date"] = date.today()
    holdings_df["Cost Basis"] = convert_to_base(
        df=holdings_df,
        value_col="Cost Basis",
        currency_col="currency",
        date_col="date",
        base_currency=base_currency,
        rates_pivot=rates_pivot,
    )
    holdings_df["Market Value"] = holdings_df["Current Price"] * holdings_df["Position"]
    holdings_df.loc[
        holdings_df["currency"] == "GBP", "Market Value"
    ] /= 100  # Adjust for pence
    holdings_df["Market Value"] = convert_to_base(
        df=holdings_df,
        value_col="Market Value",
        currency_col="currency",
        date_col="date",
        base_currency=base_currency,
        rates_pivot=rates_pivot,
    )

    holdings_df["Unrealised P&L"] = (
        holdings_df["Market Value"] - holdings_df["Cost Basis"]
    )
    holdings_df["Weight"] = (
        holdings_df["Market Value"] / holdings_df["Market Value"].sum()
    )
    holdings_df.drop(columns="date", inplace=True)
    return holdings_df


@st.cache_data(show_spinner=False)
# if performance is ok, no need to cache
def build_daily_holding() -> pd.DataFrame:
    """
    Build daily_holdings_df:
    date, quantity, symbol, currency
    """

    tx_df = fetch_transaction()

    tx_df["net_quantity"] = tx_df["quantity"] * (1 - 2 * tx_df["action"])

    # adjust net_quantity with stock splits
    stock_events_df = fetch_stock_event()
    stock_events_df.rename(columns={"date": "ex_date"}, inplace=True)
    stock_splits_df = stock_events_df[stock_events_df["eventType"] == 0]

    merged = tx_df.merge(stock_splits_df, on="symbol", how="left")
    merged = merged[merged["ex_date"] > merged["date"]]

    cumulative_ratios = (
        merged.groupby(["symbol", "date"])["amount"]
        .prod()
        .reset_index()
        .rename(columns={"amount": "cumulative_split_ratio"})
    )
    tx_df = tx_df.merge(cumulative_ratios, on=["symbol", "date"], how="left")
    tx_df["cumulative_split_ratio"] = pd.to_numeric(
        tx_df["cumulative_split_ratio"], errors="coerce"
    )
    tx_df["cumulative_split_ratio"] = tx_df["cumulative_split_ratio"].fillna(1.0)
    tx_df["net_quantity"] = tx_df["net_quantity"] * tx_df["cumulative_split_ratio"]

    tx_df.drop(columns=["quantity", "transactionID", "UID", "action"], inplace=True)
    daily_holdings_df = (
        tx_df.groupby(by=["date", "symbol"])["net_quantity"].sum().reset_index()
    )
    # Add currencies for .JPY, .EU, .UK, etc...
    daily_holdings_df = assign_currency(daily_holdings_df)

    daily_holdings_df.set_index(["date", "symbol"], inplace=True)

    today = pd.Timestamp.today().date()
    results = []
    for symbol, group in daily_holdings_df.groupby(level="symbol"):
        start_date = group.index.get_level_values("date").min()
        idx = pd.date_range(start=start_date, end=today, freq="D").date

        net_qty = group["net_quantity"]
        net_qty.index = net_qty.index.droplevel("symbol")

        net_qty = net_qty.reindex(idx, fill_value=0)
        quantity = net_qty.cumsum()
        quantity = quantity[quantity > 0]

        result = quantity.reset_index()
        result.columns = ["date", "quantity"]
        result["symbol"] = symbol
        result["currency"] = group["currency"].iloc[0]

        results.append(result)

    daily_holdings_df = pd.concat(results, ignore_index=True)
    daily_holdings_df.set_index(["date", "symbol"], inplace=True)
    return daily_holdings_df


@st.cache_data(show_spinner=False)
def build_allocation(holding_df: pd.DataFrame) -> pd.DataFrame:
    allocation = holding_df.copy()[["Symbol", "Sector", "Market Value"]]
    multi_mask = allocation["Sector"] == "Multi"
    multi = allocation[multi_mask]["Symbol"].tolist()
    tmp = []
    for etf in multi:
        base = allocation.loc[allocation["Symbol"] == etf, "Market Value"].values[0]
        weightings = yf.Ticker(etf).funds_data.sector_weightings
        for sector, weight in weightings.items():
            tmp.append(
                {
                    "Symbol": etf,
                    "Sector": SECTOR_CASE_MAP[sector],
                    "Market Value": base * weight,
                }
            )
    allocation = allocation[~multi_mask]
    allocation = pd.concat([allocation, pd.DataFrame(tmp)])
    return allocation


@st.cache_data(show_spinner=False)
def portfolio_time_weighted_return(df: pd.DataFrame) -> pd.DataFrame:
    df["daily_return"] = (
        df["base_value_before_tx"] / df["base_value_after_tx"].shift(1) - 1
    )
    df.loc[df.index[0], "daily_return"] = 0
    df["TWR"] = ((1 + df["daily_return"]).cumprod() - 1) * 100
    return df


@st.cache_data(show_spinner=False)
def portfolio_daily_return(df: pd.DataFrame) -> pd.DataFrame:
    df["daily_return"] = (
        df["base_value_before_tx"] / df["base_value_after_tx"].shift(1)
    ) - 1
    df.loc[df.index[0], "daily_return"] = 0
    returns_series = df["daily_return"].fillna(0).replace([np.inf, -np.inf], 0)
    returns_series.index = pd.to_datetime(returns_series.index)
    return returns_series
