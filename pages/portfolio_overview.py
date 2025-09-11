import streamlit as st
import plotly.express as px
import pandas as pd


def tab_contents(tab):
    st.markdown(f"### Portfolio Allocation by {tab}")
    df = px.data.tips()
    fig = px.pie(df, values="tip", names="day")
    st.plotly_chart(fig, key=tab)


st.title("Portfolio Overview")
"- Total Portfolio value"
"- Let user choose base currency (HKD / USD)"

tab1, tab2, tab3, tab4 = st.tabs(["Assets", "Sectors", "Classes", "Currencies"])

with tab1:
    df = pd.DataFrame(
        {
            "Last Price": 210,
            "Position": 100,
            "Market Value": 210 * 100,
        },
        index=["AAPL"],
    )
    df.index.name = "Ticker"
    st.dataframe(df)

with tab2:
    tab_contents("Sector")

with tab3:
    tab_contents("Asset Class")

with tab4:
    tab_contents("Currency")
