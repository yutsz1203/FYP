import json

import pandas as pd
import streamlit as st
import yfinance as yf
from pypfopt import expected_returns, risk_models
from pypfopt.efficient_frontier import EfficientFrontier


@st.cache_data(show_spinner=False)
def download_prices(tickers: list[str], period: str, interval: str) -> pd.DataFrame:
    """
    Download prices for certain period using certain interval data.

    Input:
    tickers (list(str)): ["VOO", "GLD", "IBIT"]
    period (str): "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    interval (str): "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

    Output:
    prices (DataFrame): rows are dates, columns are tickers
    """
    prices = yf.download(tickers, period=period, interval=interval, auto_adjust=True)[
        "Close"
    ]

    return prices


def get_optimal_weights(weights) -> pd.DataFrame:
    weights_df = pd.DataFrame(weights.items(), columns=["Asset", "Weight"])
    return weights_df


def portfolio_optimize(
    risk_preference: str, asset_list: list
) -> tuple[pd.DataFrame, dict]:
    """
    risk_preferences
    1. Capital Preservation
        70% bond, 20% broad market, 5% sector, 5% commodity
    2. Conservative
        55% bond, 30% market, 10% sector, 5% commodity
    3. Balanced
        40% bond, 40% market, 15% sector, 5% commodity
    4. Growth
        25% bond, 45% market, 20% sector, 10% commodity
    5. Aggresive Growth
        10% bond, 50% market, 30% sector, 10% commodity
    """
    period = "5y"
    interval = "1mo"

    with open("data/model_portfolios.json", "r") as f:
        model_portfolios = json.load(f)
        model_weights = model_portfolios[risk_preference]

    market_map = {"VOO": "US", "2800.HK": "HK", "VXUS": "World"}
    sector_map = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLV": "Health Care",
        "XLY": "Consumer(Non-Essential)",
        "XLP": "Consumer(Essential)",
        "XLI": "Industrials",
        "XLE": "Energy",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLC": "Communication",
    }
    commodity_map = {
        "GLD": "Gold",
        "SLV": "Silver",
        "USO": "Oil",
        "DBB": "Industrial Metals",
        "DBA": "Agriculture",
        "DJP": "Broad",
        "IBIT": "Bitcoin",
    }

    asset_set = set(asset_list)
    market_asset = list(asset_set & set(market_map.keys()))
    sector_asset = list(asset_set & set(sector_map.keys()))
    commodity_asset = list(asset_set & set(commodity_map.keys()))

    market_ef, sector_ef, commodity_ef = None, None, None

    if market_asset:
        market_ef = generate_ef(
            model_weights, market_asset, "Market", period, interval, market_map
        )

    if sector_asset:
        sector_ef = generate_ef(
            model_weights, sector_asset, "Sector", period, interval, sector_map
        )

    if commodity_asset:
        commodity_ef = generate_ef(
            model_weights, commodity_asset, "Commodity", period, interval, commodity_map
        )

    if not sector_asset:
        model_weights["Market"] += model_weights["Sector"]
        model_weights["Sector"] = 0

    if not commodity_asset:
        model_weights["Market"] += model_weights["Commodity"]
        model_weights["Commodity"] = 0

    # Conservative
    if risk_preference == "Capital Preservation" or risk_preference == "Conservative":
        if market_ef:
            market_ef.min_volatility()
        if sector_ef:
            sector_ef.min_volatility()
        if commodity_ef:
            commodity_ef.min_volatility()
    # Balanced
    elif risk_preference == "Balanced":
        if market_ef:
            market_ef.max_sharpe()
        if sector_ef:
            sector_ef.max_sharpe()
        if commodity_ef:
            commodity_ef.max_sharpe()
    # Aggresive
    else:
        if market_ef:
            market_ef.efficient_risk(0.4)
        if sector_ef:
            sector_ef.efficient_risk(0.4)
        if commodity_ef:
            commodity_ef.efficient_risk(0.4)

    market_optimal, sector_optimal, commodity_optimal = None, None, None
    if market_ef:
        market_optimal = get_optimal_weights(market_ef.clean_weights())
        market_optimal["Weight"] *= model_weights["Market"]
    if sector_ef:
        sector_optimal = get_optimal_weights(sector_ef.clean_weights())
        sector_optimal["Weight"] *= model_weights["Sector"]
    if commodity_ef:
        commodity_optimal = get_optimal_weights(commodity_ef.clean_weights())
        commodity_optimal["Weight"] *= model_weights["Commodity"]

    recommended_portfolio = pd.concat(
        [
            pd.DataFrame([{"Asset": "BND", "Weight": model_weights["Bond"]}]),
            market_optimal,
            sector_optimal,
            commodity_optimal,
        ]
    )
    return recommended_portfolio, model_weights


def generate_ef(model_weights, asset_list, asset_type, period, interval, mapping):
    prices = download_prices(asset_list, period, interval)
    mu = expected_returns.mean_historical_return(prices, frequency=12)
    S = risk_models.sample_cov(prices, frequency=12)
    ef = EfficientFrontier(mu, S)

    constraint_lower, constraint_upper = {}, {}
    minimum = model_weights[asset_type] / len(asset_list)
    for asset in asset_list:
        constraint_lower[mapping[asset]] = minimum
        constraint_upper[mapping[asset]] = 1

    ef.add_sector_constraints(mapping, constraint_lower, constraint_upper)

    return ef
