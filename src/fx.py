import pandas as pd


def get_rates_pivot(rates_df: pd.DataFrame) -> pd.DataFrame:
    """
    rate_df schema: date, currency, rate
    """
    return rates_df.pivot(index="date", columns="currency", values="rate")


def to_usd(
    value_series: pd.Series,
    currency_series: pd.Series,
    date_series: pd.Series,
    rates_pivot: pd.DataFrame,
) -> pd.Series:
    """
    Converts any value series to USD using the anchor currency pattern.

    Parameters:
        value_series:    pd.Series of monetary values
        currency_series: pd.Series of currency codes (e.g. "HKD", "USD")
        date_series:     pd.Series of dates for rate lookup
        rates_pivot:     output of get_rates_pivot()

    Returns: pd.Series of values in USD
    """
    rates_on_date = rates_pivot.reindex(date_series.values)
    rates_on_date.index = value_series.index

    usd_rate = pd.Series(1.0, index=value_series.index)

    usd_rate[currency_series == "HKD"] = rates_on_date["USD/HKD"]
    usd_rate[currency_series == "EUR"] = rates_on_date["USD/EUR"]
    usd_rate[currency_series == "GBP"] = rates_on_date["USD/GBP"]
    usd_rate[currency_series == "JPY"] = rates_on_date["USD/JPY"]
    usd_rate[currency_series == "CNY"] = rates_on_date["USD/CNY"]

    return value_series / usd_rate


def to_base_currency(
    value_usd_series: pd.Series,
    date_series: pd.Series,
    base_currency: str,
    rates_pivot: pd.DataFrame,
) -> pd.Series:
    """
    Converts a USD value series to the user's chosen base currency.

    Parameters:
        value_usd_series: pd.Series of values already in USD
        date_series:      pd.Series of dates for rate lookup
        base_currency:    str, e.g. "USD", "HKD", "EUR"
        rates_pivot:      output of get_rates_pivot()

    Returns: pd.Series of values in base currency
    """

    if base_currency == "USD":
        return value_usd_series

    pair_map = {
        "HKD": "USD/HKD",
        "EUR": "USD/EUR",
        "GBP": "USD/GBP",
        "JPY": "USD/JPY",
        "CNY": "USD/CNY",
    }

    pair = pair_map[base_currency]
    rates_on_date = rates_pivot.reindex(date_series.values)
    rates_on_date.index = value_usd_series.index

    return value_usd_series * rates_on_date[pair]


def convert_to_base(
    df: pd.DataFrame,
    value_col: str,
    currency_col: str,
    date_col: str,
    base_currency: str,
    rates_pivot: pd.DataFrame,
) -> pd.Series:
    """
    Full conversion pipeline — local currency → USD → base currency.
    Works on any DataFrame that has a value, currency, and date column.

    Parameters:
        df:            any DataFrame
        value_col:     name of the column containing monetary values
        currency_col:  name of the column containing currency codes
        date_col:      name of the column containing dates
        base_currency: user's chosen display currency
        rates_pivot:   output of get_rates_pivot()

    Returns: pd.Series of converted values in base currency
    """
    value_usd = to_usd(df[value_col], df[currency_col], df[date_col], rates_pivot)

    return to_base_currency(value_usd, df[date_col], base_currency, rates_pivot)


def assign_currency(df: pd.DataFrame, symbol_col="symbol") -> pd.DataFrame:
    """
    Assign a currency column in the df.

    Parameters:
        df: pd.DataFrame

    Returns:
        df: pd.DataFrame with a currency column.
    """
    result = df.copy()
    result["currency"] = "USD"
    result["pence_adjusted"] = (
        False  # for adjusting .L stocks as they are displaying in pence, instead of pound
    )

    exchange_currency_map = {
        r"\.HK$": "HKD",
        r"\.PA$|\.AS$|\.DE$|\.BR$|\.MI$|\.MC$": "EUR",
        r"\.L$": "GBP",
        r"\.T": "JPY",
        r"\.SS$|\.SZ$": "CNY",
    }

    for pattern, currency in exchange_currency_map.items():
        mask = result[symbol_col].str.contains(pattern, regex=True, na=False)
        result.loc[mask, "currency"] = currency

        if currency == "GBP":
            result.loc[mask, "pence_adjusted"] = True

    return result
