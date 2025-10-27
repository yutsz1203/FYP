import streamlit as st

# Define the pages
home_page = st.Page("pages/home_page.py", title="Home")
portfolio_overview = st.Page("pages/portfolio_overview.py", title="Portfolio Overview")
portfolio_returns = st.Page("pages/portfolio_returns.py", title="Portfolio Returns")
risk_analysis = st.Page("pages/risk_analysis.py", title="Risk Analysis Tools")
transactions = st.Page("pages/transactions.py", title="Transactions")

# Set up navigation
pg = st.navigation(
    [
        home_page,
        portfolio_overview,
        portfolio_returns,
        risk_analysis,
        transactions,
    ]
)

# Run the selected page
pg.run()
