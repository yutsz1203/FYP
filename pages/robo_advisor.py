# display portfolio components, past return performance graph, risk metrics, simulating value growth

import altair as alt
import plotly.express as px
import quantstats as qs
import streamlit as st

from const import RETURN_TEXT
from helpers import adjust_period, create_chart
from src.mpt import get_optimal_weights, get_optimised_performance
from src.holding import get_holdings
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
                    "Buy", format="-$%.2f"
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
                    "Buy", format="$%.2f"
                )
            },
        )
    else:
        rebalance_df = rebalance_NoSell(current, target)
        rebalance_df.loc[-1] = ["Total", rebalance_df["Investment Action"].sum()]
        st.dataframe(
            data=rebalance_df,
            hide_index=True,
            column_config={
                "Investment Action": st.column_config.NumberColumn(
                    "Buy", format="$%.2f"
                )
            },
        )


holdings_df = get_holdings("HKD")
weights_df = get_optimal_weights()
weights_df = weights_df[weights_df["Weight"] != 0]
rebalance = rebalance_check(holdings_df[["Symbol", "Weight"]], weights_df)
ret, std, sharpe = get_optimised_performance()

st.set_page_config(page_icon="💼", layout="centered")
st.title("💼 Robo Advisor")
if rebalance:
    st.warning("Rebalancing available")
    if st.button("Show rebalance", type="primary"):
        rebalance_dialog(
            holdings_df[["Symbol", "Weight", "Market Value", "Current Price"]],
            weights_df,
        )

st.markdown("### Optimised Portfolio")
st.write("Risk Preference: Moderate")
col1, col2, col3 = st.columns(3)
with col1:
    st.write(f"Expected Return: {ret:.4f}")
with col2:
    st.write(f"Expected Volatility: {std:.4f}")
with col3:
    st.write(f"Sharpe Ratio: {sharpe:.4f}")

optimised_fig = px.pie(weights_df, values="Weight", names="Asset")
optimised_fig.update_traces(
    hovertemplate="Asset=%{label}<br>Weight=%{value}<extra></extra>",
    textfont_size=16,
)
optimised_fig.update_layout(legend_font_size=16)

st.plotly_chart(optimised_fig, key="optimised_chart")
st.markdown("### Detailed Allocation")
st.dataframe(weights_df)

st.markdown("### Historical Returns")
returns = historical_return(tickers=weights_df["Asset"].tolist())
weights_df = weights_df.set_index("Asset")
daily_return = returns[weights_df.index].dot(weights_df)
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
daily_return["Daily Return"] = ((1 + daily_return["Daily Return"]).cumprod() - 1) * 100
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
