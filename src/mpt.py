import matplotlib.pyplot as plt
import pandas as pd
import quantstats as qs
import streamlit as st
import yfinance as yf
from pypfopt import expected_returns, plotting, risk_models
from pypfopt.efficient_frontier import EfficientFrontier


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


def demo():
    tickers = ["VOO", "2800.HK", "GLD", "QQQ", "IBIT"]  # passed from Fred's input
    period = "5y"
    interval = "1mo"
    prices = download_prices(tickers, period, interval)

    mu = expected_returns.mean_historical_return(prices, frequency=12)
    S = risk_models.sample_cov(prices, frequency=12)

    ef = EfficientFrontier(mu, S)

    # Conservative - efficient_return() minimises risk for a given target return
    ef_conservative = ef.deepcopy()
    target_return = 0.05  # passed from Fred's input
    weights_conservative = ef_conservative.efficient_return(target_return)
    ret_conservative, std_conservative, sharpe_conservative = (
        ef_conservative.portfolio_performance()
    )

    print(
        f"Conservative: {weights_conservative}, Return {ret_conservative}, Vol {std_conservative}, Sharpe {sharpe_conservative}"
    )

    print(ef_conservative.clean_weights(rounding=4).items())

    # Moderate - max_sharpe() optimises for maximal Sharpe ratio
    ef_moderate = ef.deepcopy()
    weights_moderate = ef_moderate.max_sharpe()
    ret_moderate, std_moderate, sharpe_moderate = ef_moderate.portfolio_performance()

    print(
        f"Moderate: {weights_moderate}, Return {ret_moderate}, Vol {std_moderate}, Sharpe {sharpe_moderate}"
    )

    # Aggresive - efficient_risk() maximises return for a given target risk
    ef_aggresive = ef.deepcopy()
    weights_aggresive = ef_aggresive.efficient_risk(1)
    ret_aggresive, std_aggresive, sharpe_aggresive = (
        ef_aggresive.portfolio_performance()
    )

    print(
        f"Aggresive: {weights_aggresive}, Return {ret_aggresive}, Vol {std_aggresive}, Sharpe {sharpe_aggresive}"
    )

    # plot graph
    fig, ax = plt.subplots()
    plotting.plot_efficient_frontier(ef, ax=ax, show_assets=True, show_tickers=True)

    ax.scatter(
        std_conservative,
        ret_conservative,
        marker="*",
        s=100,
        c="r",
        label="Conservative",
    )
    ax.scatter(std_moderate, ret_moderate, marker="*", s=100, c="g", label="Moderate")
    ax.scatter(
        std_aggresive, ret_aggresive, marker="*", s=100, c="b", label="Aggresive"
    )

    ax.legend()
    plt.tight_layout()
    return plt


@st.cache_resource(show_spinner=False)
def generate_ef() -> EfficientFrontier:
    tickers = [
        "VOO",
        "2800.HK",
        "GLD",
        "QQQ",
        "IBIT",
        "BND",
    ]  # passed from Fred's input
    period = "10y"
    interval = "1mo"
    prices = download_prices(tickers, period, interval)

    mu = expected_returns.mean_historical_return(prices, frequency=12)
    S = risk_models.sample_cov(prices, frequency=12)

    ef = EfficientFrontier(mu, S)

    # Conservative - efficient_return() minimises risk for a given target return
    ef_conservative = ef.deepcopy()
    target_return = 0.05  # passed from Fred's input
    weights_conservative = ef_conservative.efficient_return(target_return)

    # Moderate - max_sharpe() optimises for maximal Sharpe ratio
    ef_moderate = ef.deepcopy()
    weights_moderate = ef_moderate.max_sharpe()

    # Aggresive - efficient_risk() maximises return for a given target risk
    ef_aggresive = ef.deepcopy()
    weights_aggresive = ef_aggresive.efficient_risk(1)

    return ef_conservative


def get_optimal_weights() -> pd.DataFrame:
    ef = generate_ef()
    weights = ef.clean_weights()
    weights_df = pd.DataFrame(weights.items(), columns=["Asset", "Weight"])
    return weights_df


def get_optimised_performance():
    ef = generate_ef()
    ret, std, sharpe = ef.portfolio_performance()
    return ret, std, sharpe


"""
## expected return calculation
1. mean_historical_return
2. ema_historical_return
3. capm_return

## covariance matrix estimation
1. sample_cov
2. semicovariance
3. exp_cov

## optimal weights based on risk preferences
Conservative: min_volatility (minimises volatility) / efficient_return (minimises volatility for a given target return)
Moderate: max_sharpe (maximises sharpe ratio, returns per unit risk)
Aggressive: efficient_risk (maximises return for a given target risk)
"""
