import pandas as pd
import quantstats as qs
import statsmodels.api as sm
import streamlit as st
import yfinance as yf

from src.holding import get_holdings


def portfolio_historical(
    holdings_df: pd.DataFrame, period: str, interval: str
) -> pd.Series:
    """
    Get returns for certain period using certain interval data.

    Input:
    holdings_df (df): ['symbol', 'quantity', 'currentPrice', 'weight']
    period (str): "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", and "max"
    interval (str): "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

    Output:
    portfolio_return (series): Index(pd.DateTimeIndex) Value(Float)
    e.g.
    Date
    2021-05-01   -0.029245
    """

    tickers = holdings_df["Symbol"].tolist()
    total_value = holdings_df["Market Value"].sum()
    holdings_df["weight"] = holdings_df["Market Value"] / total_value
    weights = holdings_df["weight"].tolist()

    data = yf.download(tickers, period=period, interval=interval, auto_adjust=True)
    data = data["Close"]

    returns = data.pct_change()
    returns = returns.loc[returns.notna().any(axis=1)]

    # w_i = portfolio weights
    # w_tilda{i,t} = w_i / sum(w_j), R_{p,t} = sum (w_tilda{i,t} * R_{i,t})
    # R_{p,t} = sum(w_i * R_{i,t}) / sum(w_j)
    weighted = returns.mul(weights, axis=1)
    portfolio_return = weighted.sum(axis=1) / weighted.notna().mul(weights, axis=1).sum(
        axis=1
    )
    portfolio_return.name = "RP"

    return portfolio_return


@st.cache_data(show_spinner=False)
def get_indv_returns(symbols, cache_key, period="1y"):
    return qs.utils.download_returns(symbols, period=period)


@st.cache_data(show_spinner=False)
def get_benchmarks_volatility(period="1y"):
    benchmark_returns = qs.utils.download_returns(
        ["^HSI", "^IXIC", "^GSPC", "XWD.TO"], period=period
    )
    return benchmark_returns.volatility()


@st.cache_data(show_spinner=False)
def get_msci_returns(period="1y"):
    return qs.utils.download_returns("XWD.TO", period=period)


@st.cache_data(show_spinner=False)
def get_betas(returns, benchmark_return):
    betas = []
    for col in returns.columns:
        beta = qs.stats.greeks(returns[col], benchmark_return)["beta"]
        betas.append({"symbol": col, "beta": beta.round(2)})
    df = pd.DataFrame(betas)
    return df


@st.cache_data(show_spinner=False)
def get_corr_matrix(returns):
    return returns.corr()


@st.cache_data(show_spinner=False)
def generate_report(returns, benchmark, output_path):
    qs.reports.html(returns, benchmark=benchmark, output=output_path)


@st.cache_data(show_spinner=False)
def factor_analysis(period):
    holdings_df = get_holdings()
    portfolio_return = portfolio_historical(holdings_df, period, "1mo")
    portfolio_return.index = portfolio_return.index.map(
        lambda x: int(x.strftime("%Y%m"))
    )

    fama_df = pd.read_csv("data/F-F_Research_Data_5_Factors_2x3.csv", index_col=0)
    fama_df = fama_df / 100

    df = fama_df.join(portfolio_return).dropna()
    df["RP-RF"] = df["RP"] - df["RF"]

    y = df["RP-RF"]
    X = df[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]]
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()
    return model
