import streamlit as st

st.set_page_config(page_title="Home", page_icon="🏠", layout="centered")
# Main page content
st.title("Robo-advisor and Portfolio Tracking System")
st.write(
    "The Robo-Advisor and Portfolio Tracking System project aims to develop an automated investment advice platform that utilizes data science techniques to provide personalized investment recommendations to users. The system considers factors such as users' risk preferences, cash flows, financial goals, and market conditions to create recommendation on an investment portfolio. By implementing portfolio allocation and leveraging historical market data, the robo-advisor system aims to assist users in making informed investment decisions. The project consists of two main components."
)
st.markdown("### Robo-advisor")
st.write(
    "Using modern portfolio theory and optimization algorithms, the robo-advisor system will generate customized investment portfolios by considering users' available cash flows, financial goals and risk constraints. The system will take into account diversification principles and rebalancing strategies to optimize expected portfolio performance over time."
)
st.markdown("### Portfolio Tracking System")
st.markdown(
    "The portfolio tracking component of the system will provide users with a comprehensive view of their investment portfolios. It will offer automatic updates on portfolio values and provide performance tracking features such as calculating portfolio returns and measuring performance against market benchmarks. The system will also include risk analysis tools to assess the risk profile of the portfolio, including metrics such as volatility, beta, standard deviation, value-at-risk (VaR), correlation analysis, and factor analysis. Additionally, users will have the ability to record and track their buy/sell transactions within the portfolio tracking system, including details such as quantity, price, and date. The system will maintain a transaction history, allowing users to review their trading activity and monitor the impact on portfolio performance."
)
st.write(
    "By combining the robo-advisor and portfolio tracking components, the system aims to empower users with personalized investment advice and comprehensive tracking capabilities. This will enable users to make informed investment decisions, monitor their portfolios effectively, and optimize their investment strategies based on their financial goals and risk preferences."
)
st.markdown("### Functions to add ...")
st.write("Taxes: Capital gain, Witholding (Dividend)")
st.write(
    "Incorporating taxes and dividends in calculation of portfolio values and returns"
)
