import streamlit as st
import pandas as pd

st.title("Portfolio Returns and Performance")

tab1, tab2 = st.tabs(["Portfolio Returns", "Performance against market benchmarks"])

with tab1:
    "- Calculating portfolio returns"
    "- Periods: 1wk, mtd, 1m, 3m, ytd, 1y, All "

with tab2:
    "- Measuring performance against market benchmarks (^GSPC, ^HSI, ^IXIC)"
