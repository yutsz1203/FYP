import altair as alt
import streamlit as st

from utils import (
    calcReturns,
    calcWeightedReturns,
    cumulativeReturn,
    cumulativeValue,
    fetchData,
    periods,
)

st.set_page_config(page_icon="📈", layout="centered")

st.title("Portfolio Returns and Performance")

tab1, tab2 = st.tabs(["Portfolio Returns", "Performance against market benchmarks"])

with tab1:
    portfolio = fetchData(["AAPL", "MSFT", "GOOG"])
    weights = [0.3, 0.4, 0.3]
    portfolio_returns = calcWeightedReturns(calcReturns(portfolio), weights)
    portfolio_cumulative_returns = cumulativeReturn(portfolio_returns)
    nearest = alt.selection_point(
        nearest=True, on="pointerover", fields=["Date"], empty=False
    )
    chart_data = alt.Chart(portfolio_cumulative_returns).transform_calculate(
        Returns_Percent='datum.Returns + "%"'
    )
    line = chart_data.mark_line(strokeWidth=2).encode(x="Date:T", y="Returns:Q")
    points = (
        chart_data.mark_circle(size=90)
        .encode(
            x="Date:T",
            y="Returns:Q",
            opacity=alt.condition(nearest, alt.value(1), alt.value(0)),
            tooltip=[
                alt.Tooltip("Date:T", title="Date"),
                alt.Tooltip("Returns_Percent:N", title="Returns"),
            ],
        )
        .add_params(nearest)
    )
    chart = alt.layer(line, points).properties(width=600, height=400)

    st.altair_chart(chart)
    st.pills("Time period", periods, key="returns")

    st.write("May exclude returns from Bonds")

with tab2:
    benchmarks = fetchData(["2800.HK", "SPY"])
    benchmarks_cumulative_return = cumulativeValue(benchmarks)
    st.line_chart(
        benchmarks_cumulative_return,
        x_label="Date",
        y_label="Values",
    )
    st.pills("Time period", periods, key="benchmark")
    st.write(
        "Let user to choose which index to include in the comparison. If possible, include individual stocks for comparison."
    )
