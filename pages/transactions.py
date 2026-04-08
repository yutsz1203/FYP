from datetime import datetime

import streamlit as st

from helpers import bump_cache_key, get_start_date
from src.db import db_connect, mariadb_connect
from src.transaction_src import get_tx, insert_tx

st.set_page_config(page_title="Transactions", page_icon="🧮", layout="wide")
st.session_state["cache_key"] = datetime.now().strftime("%Y%m%d-%H%M%S")
conn = db_connect()
maria_conn = mariadb_connect()


tx_df = get_tx(conn)
tx_df.sort_values("Date", inplace=True)

# Main page content
st.title("🧮 Transactions")
st.markdown("### Record a transaction")
with st.form("add_transactions", clear_on_submit=True):
    col1, col2, col3, col4, col5, col6, col7 = st.columns(
        [4, 2, 2, 2, 2, 2, 1], vertical_alignment="bottom"
    )
    date = col1.date_input("Transaction date")
    action = col2.selectbox("Action", ["Buy", "Sell"])
    ticker = col3.text_input("Ticker")
    price = col4.number_input("Price", min_value=0.0)
    quantity = col5.number_input("Quantity", min_value=0.0)
    commission = col6.number_input("Commissions", min_value=0.0)
    add_button = col7.form_submit_button("Add", "Add")

    if add_button:
        action = int(action == "Sell")  # 0 for buy, 1 for sell
        insert_tx(
            (
                st.session_state["lastrowid"],
                date,
                ticker.upper(),
                price,
                quantity,
                action,
                commission,
                1,
            ),
            maria_conn,
        )
        st.session_state["lastrowid"] += 1
        bump_cache_key()
        st.cache_data.clear()
        st.cache_resource.clear()
        st.rerun()

st.markdown("### Transaction History")
with st.form("transaction_history"):
    col1, col2, col3 = st.columns([6, 6, 1], vertical_alignment="bottom")
    from_date = col1.date_input("From", value=get_start_date())
    to_date = col2.date_input("To")
    filter_button = col3.form_submit_button("Filter")

    tx_df["Action"] = tx_df["Action"].replace({0: "Buy", 1: "Sell"})
    if filter_button:
        st.dataframe(tx_df[tx_df["Date"].between(from_date, to_date)], hide_index=True)
    else:
        st.dataframe(tx_df, hide_index=True)
