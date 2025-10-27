import streamlit as st
import plotly.express as px
import pandas as pd
from utils import fetchData, periods

st.set_page_config(page_icon="📊", layout="centered")


def tab_contents(tab):
    st.markdown(f"### Portfolio Allocation by {tab}")
    df = px.data.tips()
    fig = px.pie(df, values="tip", names="day")
    st.plotly_chart(fig, key=tab)


st.title("Portfolio Overview")
st.markdown("### Portfolio Value")
base_currency = st.selectbox("Choose base currency", ("HKD", "USD"), width=150)

if base_currency == "HKD":
    st.markdown("#### Portfolio Value: HK$ XXXX")
elif base_currency == "USD":
    st.markdown("#### Portfolio Value: $ XXXX")

df = fetchData(["AAPL"])
st.line_chart(df, x_label="Date", y_label="Portfolio Value")

period = st.pills("Time period", periods, key="value", default=periods[6])

tab1, tab2, tab3, tab4 = st.tabs(["Assets", "Sectors", "Classes", "Currencies"])

with tab1:
    df = pd.DataFrame(
        {
            "Last Price": 210,
            "Position": 100,
            "Market Value": 210 * 100,
            "Cost Basis": 180 * 100,
            "P&L": (210 - 180) * 100,
        },
        index=["AAPL"],
    )
    df.index.name = "Ticker"
    st.dataframe(df)

with tab2:
    tab_contents("Sector")

with tab3:
    tab_contents("Asset Class")
    st.markdown("Asset Classes: Stocks, Bonds, Commodities, Cryptocurrencies")

with tab4:
    tab_contents("Currency")
    st.write("Currencies: HKD, USD")
