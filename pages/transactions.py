import streamlit as st

# Main page content
st.title("Transactions")
st.markdown("### Record a transaction")
with st.form("add_transactions"):
    col1, col2, col3, col4, col5, col6, col7 = st.columns(
        7, vertical_alignment="bottom"
    )
    date = col1.date_input("Transaction date")
    action = col2.selectbox("Action", ["Buy", "Sell"])
    ticker = col3.text_input("Ticker")
    price = col4.number_input("Price", min_value=0.0)
    quantity = col5.number_input("Quantity", min_value=0.0)
    commission = col6.number_input("Commissions", min_value=0.0)
    action_button = col7.form_submit_button("Add", "Add")

st.markdown("### Transaction History")
