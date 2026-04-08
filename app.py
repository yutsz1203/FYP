import streamlit as st

# Define the pages
home_page = st.Page("pages/home_page.py", title="Home")
portfolio_overview = st.Page("pages/portfolio_overview.py", title="Portfolio Overview")
portfolio_returns = st.Page("pages/portfolio_returns.py", title="Portfolio Returns")
risk_analysis = st.Page("pages/risk_analysis.py", title="Risk Analysis Tools")
transactions = st.Page("pages/transactions.py", title="Transactions")
robo_advisor = st.Page("pages/robo_advisor.py", title="Robo advisor")

# Set up navigation
pg = st.navigation(
    [
        home_page,
        portfolio_overview,
        portfolio_returns,
        risk_analysis,
        transactions,
        robo_advisor,
    ]
)

# Run the selected page
pg.run()
