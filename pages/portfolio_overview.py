import altair as alt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dateutil.relativedelta import relativedelta

from utils import periods

st.set_page_config(page_icon="📊", layout="centered")


@st.cache_resource(show_spinner=False)
def db_connect():
    conn = st.connection("mysql", type="sql")
    return conn


@st.cache_data(show_spinner=False)
def get_rates(_conn):
    rates_df = _conn.query("SELECT rate FROM Rate WHERE currency = 'USD';")
    return rates_df


@st.cache_data(show_spinner=False)
def get_holdings(_conn, cache_key):
    holdings_df = _conn.query(
        "SELECT h.symbol, a.currentPrice, h.quantity, h.costBasis, s.sector, c.className "
        "FROM Holding h "
        "JOIN Asset a ON h.symbol = a.symbol "
        "JOIN Class c ON a.class = c.classID "
        "JOIN Sector s ON a.sector = s.sectorID;",
        ttl=0,
    )
    return holdings_df


@st.cache_data(show_spinner=False)
def get_transactions(_conn, cache_key) -> pd.DataFrame:
    tx_df = _conn.query(
        "SELECT transactionID, date, symbol, quantity, action FROM Transaction", ttl=0
    )
    return tx_df


@st.cache_data(show_spinner=False)
def get_prices(_conn, cache_key, start, end) -> pd.DataFrame:
    price_df = _conn.query(
        f"SELECT date, symbol, close FROM Price WHERE date BETWEEN '{start}' AND '{end}'",
        ttl=0,
    )
    price_df.set_index("date", inplace=True)
    return price_df


@st.cache_data(show_spinner=False)
def get_stock_splits(_conn, cache_key) -> pd.DataFrame:
    stock_split_df = _conn.query("SELECT symbol, date, ratio FROM Stock_Split", ttl=0)
    return stock_split_df


# adjust cache_key after the add button is pressed in the transaction page
cache_key = st.session_state.get("cache_key", "v1")
conn = db_connect()
rates_df = get_rates(conn)
HKD_USD = rates_df.iloc[0, 0]

holdings_df = get_holdings(conn, cache_key)

holdings_df.columns = [
    "Symbol",
    "Current Price",
    "Position",
    "Cost Basis",
    "Sector",
    "Class",
]

holdings_df["Market Value"] = holdings_df["Current Price"] * holdings_df["Position"]

us_assets = holdings_df["Symbol"].str.isalpha()

st.title("Portfolio Overview")
st.markdown("### Portfolio Value")
base_currency = st.selectbox("Choose base currency", ("HKD", "USD"), width=150)
period = st.pills("Time period", periods, key="value", default=periods[6])

if base_currency == "HKD":
    holdings_df.loc[us_assets, "Market Value"] *= HKD_USD
    holdings_df.loc[us_assets, "Cost Basis"] *= HKD_USD
else:
    holdings_df.loc[~us_assets, "Market Value"] /= HKD_USD
    holdings_df.loc[~us_assets, "Cost Basis"] /= HKD_USD

holdings_df["Unrealised P&L"] = holdings_df["Market Value"] - holdings_df["Cost Basis"]
portfolio_value = holdings_df["Market Value"].sum()

if base_currency == "HKD":
    st.markdown(f"#### Portfolio Value: HK$ {portfolio_value:,.2f}")
elif base_currency == "USD":
    st.markdown(f"#### Portfolio Value: $ {portfolio_value:,.2f}")

# Calculating Portfolio Value
# Portfolio Value = Market Value of Positions

# Load transaction table, +quantity for BUY, -quantity for SELL
tx_df = get_transactions(conn, cache_key)
tx_df.loc[tx_df["action"] == 1, "quantity"] *= -1

# - Group by (symbol, date) and sum
tx_by_symbol_df = (
    tx_df.groupby(["symbol", "date"])["quantity"]
    .sum()
    .unstack("symbol", fill_value=0.0)
)
# print(tx_by_symbol_df)

# adjust for splitting
# - apply splits and keep a running cumprod() multiplier thereafter
start = tx_by_symbol_df.index.min()
today = pd.Timestamp.today().date()
idx = pd.date_range(start=start, end=today, freq="D").date
stock_split_df = get_stock_splits(conn, cache_key)

transactions = tx_by_symbol_df.copy()
splits = stock_split_df.copy()

tx_wide = transactions.reindex(idx).fillna(0.0)
symbols = list(tx_wide.columns)
split_pivot = pd.DataFrame(1.0, index=idx, columns=symbols)

for (sym, d), grp in splits.groupby(["symbol", "date"]):
    if sym in split_pivot.columns:
        split_pivot.loc[d, sym] = split_pivot.loc[d, sym] * grp["ratio"].prod()

# Adjusted shares at time t = F(t) x sum_{d <= t} tx(d) / F(d)
# F(t) = cumulative split factor at time t
# tx(d) = shares bought / sold on date d
F = split_pivot.cumprod()
# print(split_pivot)
# print(F)

base_tx = tx_wide / F.replace(0, np.nan)
base_tx = base_tx.fillna(0.0)

base_cum = base_tx.cumsum()
adjusted_shares = (base_cum * F).astype(float)

# print(adjusted_shares)

# adjust the start date
if period == "1W":
    start = max(start, today - pd.Timedelta(days=7))
elif period == "MTD":
    start = max(start, today.replace(day=1))
elif period == "1M":
    start = max(start, today - relativedelta(months=1))
elif period == "3M":
    start = max(start, today - relativedelta(months=3))
elif period == "YTD":
    start = max(start, today.replace(month=1, day=1))
elif period == "1Y":
    start = max(start, today - relativedelta(years=1))


price_df = get_prices(conn, cache_key, str(start), str(today))

price_wide_df = price_df.pivot(columns="symbol", values="close").sort_index()

# adjust for currency
for col in price_wide_df.columns:
    if base_currency == "HKD":
        if "." not in col:
            price_wide_df[col] *= HKD_USD
    else:
        if "." in col:
            price_wide_df[col] /= HKD_USD

# print(price_wide_df)

adjusted_shares_mask = (adjusted_shares.index >= start) & (
    adjusted_shares.index <= today
)
price_period_mask = (price_wide_df.index >= start) & (price_wide_df.index <= today)
value_per_symbol = (
    adjusted_shares[adjusted_shares_mask] * price_wide_df[price_period_mask]
)
# print(value_per_symbol)

portfolio_value = value_per_symbol.sum(axis=1).round(2)
portfolio_value.name = "Portfolio Value"

# print(portfolio_value)

st.line_chart(
    portfolio_value,
    x_label="Date",
    y_label="Portfolio Value",
)

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Assets",
        "Allocation - Sectors",
        "Allocation - Classes",
        "Allocation - Currencies",
    ]
)

# User's holdings
# Consider add a pie chart to show user's allocation by asset
with tab1:
    # Symbol, Current Price, Position, Market Value, Cost Basis, P&L
    assets_df = holdings_df[
        [
            "Symbol",
            "Current Price",
            "Position",
            "Market Value",
            "Cost Basis",
            "Unrealised P&L",
        ]
    ].copy()

    styled_assets_df = assets_df.style.format(
        {
            "Current Price": "{:,.2f}",
            "Position": "{:,.2f}",
            "Market Value": "{:,.2f}",
            "Cost Basis": "{:,.2f}",
            "Unrealised P&L": "{:,.2f}",
        }
    )

    total_p_and_l = assets_df["Unrealised P&L"].sum()

    if base_currency == "HKD":
        if total_p_and_l < 0:
            st.markdown(f"#### Unrealized P&L: :red[HK$ {total_p_and_l:,.2f}]")
        else:
            st.markdown(f"#### Unrealized P&L: :green[HK$ {total_p_and_l:,.2f}]")
    else:
        if total_p_and_l < 0:
            st.markdown(f"#### Unrealized P&L: :red[$ {total_p_and_l:,.2f}]")
        else:
            st.markdown(f"#### Unrealized P&L: :green[$ {total_p_and_l:,.2f}]")

    st.dataframe(styled_assets_df, hide_index=True)
    st.write(
        f"Note: Market Value, Cost Basis, and P&L are displayed in the chosen base currency, which is {base_currency}."
    )

# Allocation by Sector
with tab2:
    st.markdown("### Portfolio Allocation by Sector")
    sector_fig = px.pie(holdings_df, values="Market Value", names="Sector")

    sector_fig.update_traces(
        hovertemplate="Sector=%{label}<br>Market Value=%{value}<extra></extra>",
        textfont_size=16,
    )
    sector_fig.update_layout(legend_font_size=16)

    st.plotly_chart(sector_fig, key="sector_chart")

# Allocation by Asset Class
# [Stocks, Bonds, Commodities, Cryptocurrencies]
with tab3:
    st.markdown("### Portfolio Allocation by Asset Class")
    class_fig = px.pie(holdings_df, values="Market Value", names="Class")
    class_fig.update_traces(
        hovertemplate="Asset Class=%{label}<br>Market Value=%{value}<extra></extra>",
        textfont_size=16,
    )
    class_fig.update_layout(legend_font_size=16)

    st.plotly_chart(class_fig, key="class_chart")

# Allocation by Currency
# [HKD, USD]
with tab4:
    st.markdown("### Portfolio Allocation by Currency")

    us_assets_df = holdings_df[us_assets].copy()
    us_total_mv = us_assets_df["Market Value"].sum()

    hk_assets_df = holdings_df[~us_assets].copy()
    hk_total_mv = hk_assets_df["Market Value"].sum()

    if us_total_mv == 0:
        values = [hk_total_mv]
        names = ["HKD"]
    elif hk_total_mv == 0:
        values = [us_total_mv]
        names = ["USD"]
    else:
        values = [hk_total_mv, us_total_mv]
        names = ["HKD", "USD"]

    currency_fig = px.pie(values=values, names=names)

    currency_fig.update_traces(
        hovertemplate="Currency=%{label}<br>Market Value=%{value}<extra></extra>",
        textfont_size=16,
    )

    currency_fig.update_layout(legend_font_size=16)

    st.plotly_chart(currency_fig, key="currency_chart")
