# display portfolio components, past return performance graph, risk metrics, simulating value growth

import json
from datetime import date

import altair as alt
import plotly.express as px
import quantstats as qs
import streamlit as st

from const import RETURN_TEXT
from helpers import adjust_period, create_chart, fetch_price
from src.db import fetch_rate
from src.fx import assign_currency, convert_to_base, get_rates_pivot
from src.mpt import portfolio_optimize
from src.rebalance import rebalance_check, rebalance_NoSell, rebalance_Sell


@st.cache_data(show_spinner=False)
def historical_return(tickers):
    returns = qs.utils.download_returns(tickers, period="5y")
    return returns


@st.dialog("Rebalancing")
def rebalance_dialog(current, target):
    col1, col2 = st.columns([3, 2], vertical_alignment="center")
    with col1:
        st.write("Rebalance your portfolio")
    with col2:
        sell = st.toggle("With Selling")
    if sell:
        rebalance_df = rebalance_Sell(current, target)
        st.write(":red[**Sell**]")
        sell_df = rebalance_df[rebalance_df["Investment Action"] < 0]
        sell_df["Investment Action"] = -sell_df["Investment Action"]
        st.dataframe(
            sell_df,
            hide_index=True,
            column_config={
                "Investment Action": st.column_config.NumberColumn(
                    "Amount", format="-$%.2f"
                )
            },
        )
        st.write(":green[**Buy**]")
        buy_df = rebalance_df[rebalance_df["Investment Action"] > 0]
        st.dataframe(
            buy_df,
            hide_index=True,
            column_config={
                "Investment Action": st.column_config.NumberColumn(
                    "Amount", format="$%.2f"
                )
            },
        )
    else:
        rebalance_df = rebalance_NoSell(current, target)
        rebalance_df.loc[-1] = [
            "Total",
            rebalance_df["Investment Action"].sum(),
            rebalance_df["# of Shares"].sum(),
        ]
        st.dataframe(
            data=rebalance_df,
            hide_index=True,
            column_config={
                "Investment Action": st.column_config.NumberColumn(
                    "Buy", format="$%.2f"
                )
            },
        )


def load_results():
    with open("output/risk_assessment_result.json", "r") as f:
        res = json.load(f)
    return res


def get_robo_holdings(df, rate_df, user_info):
    start = user_info["created_on"]
    total_investment = user_info["total_investment"]
    assets = df["Asset"].tolist()

    initial_price = fetch_price(assets, start)
    initial_price = assign_currency(initial_price, "Ticker")
    rates_pivot = get_rates_pivot(rate_df)
    price_series = initial_price.set_index("Ticker")["Price"]
    df["Base Current Price"] = df["Asset"].map(price_series)
    initial_price["Price"] = convert_to_base(
        df=initial_price,
        value_col="Price",
        currency_col="currency",
        date_col="Date",
        base_currency="USD",
        rates_pivot=rates_pivot,
    )
    initial_price.set_index("Ticker", inplace=True)

    current_price = fetch_price(assets, str(date.today()), fetch_type="current")
    print(current_price)
    current_price = assign_currency(current_price, "Ticker")
    current_price["Price"] = convert_to_base(
        df=current_price,
        value_col="Price",
        currency_col="currency",
        date_col="Date",
        base_currency="USD",
        rates_pivot=rates_pivot,
    )
    current_price.set_index("Ticker", inplace=True)

    df.index = df["Asset"]
    df["currency"] = initial_price["currency"]
    df["Initial Price"] = initial_price["Price"]
    df["Current Price"] = current_price["Price"]
    df["Amount to buy"] = total_investment * df["Weight"]
    df["Shares to buy"] = df["Amount to buy"] / df["Initial Price"]
    df["date"] = date.today()
    df["Market Value"] = df["Current Price"] * df["Shares to buy"]
    df.loc[df["currency"] == "GBP", "Amount to buy"] /= 100  # Adjust for pence
    df.loc[df["currency"] == "GBP", "Market Value"] /= 100  # Adjust for pence

    df["Unrealised P&L"] = df["Market Value"] - df["Amount to buy"]
    df["Current Weight"] = df["Market Value"] / df["Market Value"].sum()
    df.drop(columns=["date", "Asset"], inplace=True)
    df = df.reset_index()
    return df


res = load_results()
rate_df = fetch_rate()
risk_preference = res["risk_preference"]
total_investment = res["total_investment"]
asset_list = res["asset_list"]


weights_df, model_weights = portfolio_optimize(risk_preference, asset_list)
holdings_df = get_robo_holdings(weights_df, rate_df, res)
holdings_check = holdings_df[["Asset", "Current Weight"]]
holdings_check.columns = ["Symbol", "Weight"]
weights_df = weights_df.reset_index()
rebalance = rebalance_check(holdings_check[["Symbol", "Weight"]], weights_df)


st.set_page_config(page_icon="💼", layout="wide")
st.title("💼 Robo Advisor")
tab1, tab2 = st.tabs(
    [
        "Recommended Portfolio",
        "Current Portfolio",
    ]
)
with tab1:
    st.markdown("### Recommended Portfolio")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Risk Preference: {risk_preference}")
    with col2:
        st.write(f"Total Investment Value: ${total_investment}")

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        st.write(f"Bond: {model_weights['Bond']*100:.2f}%")
    with col4:
        st.write(f"Broad Market: {model_weights['Market']*100:.2f}%")
    with col5:
        st.write(f"Sector: {model_weights['Sector']*100:.2f}%")
    with col6:
        st.write(f"Commodity: {model_weights['Commodity']*100:.2f}%")

    optimised_fig = px.pie(weights_df, values="Weight", names="Asset")
    optimised_fig.update_traces(
        hovertemplate="Asset=%{label}<br>Weight=%{value}<extra></extra>",
        textfont_size=16,
    )
    optimised_fig.update_layout(legend_font_size=16)

    st.plotly_chart(optimised_fig, key="optimised_chart")
    st.markdown("### Detailed Allocation")
    holdings_display = holdings_df[
        ["Asset", "Weight", "Amount to buy", "Shares to buy"]
    ].copy()
    holdings_display["Weight"] *= 100
    holdings_display.columns = ["Asset", "Weight (%)", "Amount to buy", "Shares to buy"]
    holdings_display = holdings_display.round(2)
    st.dataframe(holdings_display, hide_index=True)

    st.markdown("### Historical Returns")
    returns = historical_return(tickers=weights_df["Asset"].tolist())
    weights_return_df = weights_df.set_index("Asset")
    holdings_return_df = holdings_df.set_index("Asset")
    daily_return = returns[weights_return_df.index].dot(holdings_return_df[["Weight"]])
    period = st.pills(
        "Time period",
        ["1W", "MTD", "1M", "3M", "YTD", "1Y", "5Y"],
        key="value",
        default="5Y",
    )
    daily_return.index = daily_return.index.date
    start = daily_return.index.min()
    start = adjust_period(start, period)
    daily_return = daily_return[daily_return.index >= start]
    daily_return = daily_return.reset_index(names=["Date"])
    daily_return.columns = ["Date", "Daily Return"]
    daily_return["Daily Return"] = (
        (1 + daily_return["Daily Return"]).cumprod() - 1
    ) * 100
    daily_return = daily_return.round(2)

    if len(daily_return) > 0:
        period_return = daily_return.iloc[-1]["Daily Return"]
    else:
        period_return = 0
    if period_return < 0:
        st.markdown(f"### Total return {RETURN_TEXT[period]}: :red[{period_return}%]")
    else:
        st.markdown(f"### Total return {RETURN_TEXT[period]}: :green[{period_return}%]")

    base = alt.Chart(daily_return.reset_index()).encode(
        x=alt.X("Date:T", title="Date"),
        y=alt.Y(
            "Daily Return:Q",
            title="Historical Return of the Optimised Portfolio",
        ),
    )
    tooltips = [
        alt.Tooltip("Date:T", title="Date"),
        alt.Tooltip("Daily Return:N", title="Daily Return"),
    ]
    title = "Historical Return"
    chart = create_chart(daily_return, "Date", base, tooltips, title)
    st.altair_chart(chart, use_container_width=True)

with tab2:
    col7, col8, col9 = st.columns(3)
    with col7:
        st.markdown(f"#### Initial Investment: $ {total_investment:.2f}")
    with col8:
        st.markdown(f"#### Current Value: $ {holdings_df['Market Value'].sum():.2f}")
    with col9:
        total_p_and_l = holdings_df["Unrealised P&L"].sum()
        if total_p_and_l < 0:
            st.markdown(f"#### Unrealized P&L: :red[${total_p_and_l:,.2f}]")
        else:
            st.markdown(f"#### Unrealized P&L: :green[${total_p_and_l:,.2f}]")
    if rebalance:
        st.warning("Rebalancing available")
        if st.button("Show rebalance", type="primary"):
            rebalance_dialog(
                holdings_df[
                    ["Asset", "Current Weight", "Market Value", "Current Price"]
                ],
                weights_df,
            )
    current_holdings = holdings_df.copy()
    current_holdings = current_holdings[
        [
            "Asset",
            "Weight",
            "Current Weight",
            "Base Current Price",
            "Amount to buy",
            "Market Value",
            "Unrealised P&L",
        ]
    ]
    current_holdings.columns = [
        "Asset",
        "Target Weight",
        "Current Weight",
        "Current Price",
        "Cost Basis",
        "Market Value",
        "Unrealised P&L",
    ]
    st.dataframe(current_holdings, hide_index=True)
