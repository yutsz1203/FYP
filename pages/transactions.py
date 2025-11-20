import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import mariadb

st.set_page_config(page_title="Transactions", page_icon="🧮", layout="wide")


@st.cache_resource(show_spinner=False)
def db_connect():
    cfg = st.secrets["mariadb"]
    try:
        conn = mariadb.connect(
            host=cfg["host"],
            port=cfg.get("port", 6608),
            user=cfg["user"],
            password=cfg["password"],
            database="FYP",
        )
        conn.autocommit = True
        return conn.cursor()
    except mariadb.Error as e:
        st.error(f"Connection error: {e}")
        return None


conn = db_connect()


def get_tx(_conn):
    results = []
    _conn.execute(
        "SELECT * FROM FYP.Transaction",
    )
    # Drop UID Column
    lastid = 0
    for result in _conn:
        results.append(list(result)[:-1])
        lastid = result[0]
    df = pd.DataFrame(
        results,
    )
    df.columns = [
        "TId",
        "Date",
        "Symbol",
        "Price",
        "Quantity",
        "Action",
        "Commission",
    ]
    st.session_state["lastrowid"] = lastid + 1
    print(results)
    return df


def insert_tx(form, _conn):
    try:
        _conn.execute(
            "INSERT INTO FYP.Transaction VALUES (?, ?, ?, ?, ?, ?, ?, 1)", form
        )
        st.session_state["lastrowid"] += 1
        # st.cache_data.clear()
        return 1
    except mariadb.Error as e:
        st.error(e)
        return 0


def bump_cache_key():
    # Create a new key (timestamp or incrementing counter)
    st.session_state["cache_key"] = datetime.now().strftime("%Y%m%d-%H%M%S")


# Main page content
st.title("Transactions")
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
        print(st.session_state.lastrowid)
        action = int(action == "Sell")
        insert_tx(
            (
                st.session_state.lastrowid,
                date,
                ticker,
                price,
                quantity,
                action,
                commission,
            ),
            conn,
        )
        bump_cache_key()
        st.rerun()


# us stocks: can be upper case or lower case (e.g. aapl / AAPL)

# hk stocks: xxxx.hk (e.g. 0001.hk)


# If valid symbol, add entry to db.

st.markdown("### Transaction History")
with st.form("transaction_history"):
    col1, col2, col3 = st.columns([6, 6, 1], vertical_alignment="bottom")
    from_date = col1.date_input("From", value="2024-11-01")
    to_date = col2.date_input("To")
    filter_button = col3.form_submit_button("Filter")

    # Load user's transaction from db
    # test_data = {
    #     "Date": ["2025-01-20", "2025-02-20", "2025-03-20"],
    #     "Action": ["Buy", "Sell", "Buy"],
    #     "Ticker": ["AAPL", "SPLG", "RDDT"],
    #     "Price": [200.05, 70.48, 160.58],
    #     "Quantity": [100.00, 20.79, 30.54],
    #     "Commissions": [1.34, 0.34, 0.78],
    # }
    tx_df = get_tx(conn)
    # test_df = pd.DataFrame(test_data)
    # Can delete this line if "Date" field in db is already in datetime type
    # test_df["Date"] = pd.to_datetime(test_df["Date"]).dt.date

    tx_df["Action"] = tx_df["Action"].replace({0: "Buy", 1: "Sell"})
    if filter_button:
        st.dataframe(tx_df[tx_df["Date"].between(from_date, to_date)], hide_index=True)
    else:
        st.dataframe(tx_df, hide_index=True)
    # refresh transaction history when add button in add transaction form is pressed
    # if add_button:
    #     bump_cache_key()
    #     st.rerun()

    # st.dataframe(tx_df, hide_index=True)
