import streamlit as st
import pandas as pd

st.set_page_config(page_title="Transactions", page_icon="🧮", layout="wide")

# Main page content
st.title("Transactions")
st.markdown("### Record a transaction")
with st.form("add_transactions"):
    col1, col2, col3, col4, col5, col6, col7 = st.columns(
        [5, 2, 2, 2, 2, 2, 1], vertical_alignment="bottom"
    )
    date = col1.date_input("Transaction date")
    action = col2.selectbox("Action", ["Buy", "Sell"])
    ticker = col3.text_input("Ticker")
    price = col4.number_input("Price", min_value=0.0)
    quantity = col5.number_input("Quantity", min_value=0.0)
    commission = col6.number_input("Commissions", min_value=0.0)
    add_button = col7.form_submit_button("Add", "Add")

# Add checking of stock symbol
"""
us stocks: can be upper case or lower case (e.g. aapl / AAPL)

hk stocks: xxxx.hk (e.g. 0001.hk)
"""

# If valid symbol, add entry to db.

st.markdown("### Transaction History")
with st.form("transaction_history"):
    col1, col2, col3 = st.columns([7, 7, 1], vertical_alignment="bottom")
    from_date = col1.date_input("From", value="2025-01-01")
    to_date = col2.date_input("To")
    filter_button = col3.form_submit_button("Filter")

    # Load user's transaction from db
    test_data = {
        "Date": ["2025-01-20", "2025-02-20", "2025-03-20"],
        "Action": ["Buy", "Sell", "Buy"],
        "Ticker": ["AAPL", "SPLG", "RDDT"],
        "Price": [200.05, 70.48, 160.58],
        "Quantity": [100.00, 20.79, 30.54],
        "Commissions": [1.34, 0.34, 0.78],
    }

    test_df = pd.DataFrame(test_data)
    # Can delete this line if "Date" field in db is already in datetime type
    test_df["Date"] = pd.to_datetime(test_df["Date"]).dt.date

    if filter_button:
        st.dataframe(
            test_df[test_df["Date"].between(from_date, to_date)], hide_index=True
        )
    else:
        st.dataframe(test_df, hide_index=True)

    # refresh transaction history when add button in add transaction form is pressed
    if add_button:
        pass
