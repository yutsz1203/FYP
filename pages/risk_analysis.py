import streamlit as st

st.set_page_config(page_icon="⚠️", layout="centered")
# Main page content
st.title("Risk Analysis Tools")
st.write(
    "Use an overview page, with tabs or hyperlinks to specific a risk analysis tool."
)
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "Volatility",
        "Beta",
        "Value-at-risk (VaR)",
        "Correlation Analysis",
        "Factor Analysis",
    ]
)

with tab1:
    st.write(
        "A table showing volatility of user's portfolio, indices, specific portfolio (60/40), and if possible, individual stocks"
    )

with tab2:
    st.write(
        "A table showing beta and weight of individual stocks, and the beta for the whole portfolio."
    )
    st.write(
        "Consider using a more statistical approach to calculate beta instead of just fetching it from yfinance."
    )

with tab3:
    st.write("Tab is not required for this parameter, as it is just a number.")
    st.write(
        "More research is needed on how var is calculated, and dr. wong suggest simplify the correlation between stocks with estimation (country, sector, etc...)"
    )

with tab4:
    st.write("Correlation Matrix?")

with tab5:
    st.write("Python library: alphalens-reloaded")
