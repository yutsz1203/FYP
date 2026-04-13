import pandas as pd


def rebalance_check(current, target):
    # Asset list is not the same
    if list(current["Symbol"]) != list(target["Asset"]):
        return True
    for asset in list(current["Symbol"]):
        current_weight = currect.loc[current["Symbol"] == asset]["Weight"]
        target_weight = target.loc[target["Asset"] == asset]["Weight"]
        if abs(current_weight - target_weight) / target_weight >= 0.2:
            return True
    return False


def rebalance_NoSell(current, target):
    total_current = 0
    asset_list = list(target["Asset"])
    total_overweightValue = 0
    total_overweightWeight = 0
    total_underweightWeight = 0
    for asset in list(target["Asset"]):
        if asset not in list(current["Symbol"]):
            current_weight = 0
            current_value = 0
        else:
            current_weight = current.loc[current["Symbol"] == asset]["Weight"].item()
            current_value = current.loc[current["Symbol"] == asset][
                "Market Value"
            ].item()
            # print(asset, current_weight, current_value)

        target_weight = target.loc[target["Asset"] == asset]["Weight"].item()
        total_current += current_value
        # print(asset, current_weight, target_weight)
        if current_weight > target_weight:
            total_overweightValue += current_value
            total_overweightWeight += target_weight
            asset_list.remove(asset)
        else:
            total_underweightWeight += target_weight
    invest_amount = total_overweightValue / total_overweightWeight - total_current
    invest_value = []
    # invest_unit = []
    # print(asset_list)
    for asset in asset_list:
        target_weight = target.loc[target["Asset"] == asset]["Weight"].item()
        # unit_price = current.loc[current["Symbol"] == asset]["Current Price"].item()
        value_needed = invest_amount * (target_weight / (1 - total_overweightWeight))
        invest_value.append(value_needed)
        # invest_unit.append(value_needed / unit_price)
    return pd.DataFrame(
        {
            "Asset": asset_list,
            "Investment Action": invest_value,
            # "# of stocks": invest_unit,
        }
    ).round(2)


def rebalance_Sell(current, target):
    current_asset = list(current["Symbol"])
    target_asset = list(target["Asset"])
    portfolio_value = current["Market Value"].sum()
    asset_list = []
    value_list = []
    for asset in current_asset:
        if asset not in target_asset:
            asset_list.append(asset)
            value_list.append(
                -current.loc[current["Symbol"] == asset]["Market Value"].item()
            )
        else:
            current_value = current.loc[current["Symbol"] == asset][
                "Market Value"
            ].item()
            target_value = (
                target.loc[target["Asset"] == asset]["Weight"].item() * portfolio_value
            )
            if current_value > target_value:
                asset_list.append(asset)
                value_list.append(-(current_value - target_value))
    sell = sum(value_list)
    buy = 0
    for asset in target_asset:
        target_value = (
            target.loc[target["Asset"] == asset]["Weight"].item() * portfolio_value
        )
        if asset in current_asset:
            current_value = current.loc[current["Symbol"] == asset][
                "Market Value"
            ].item()
        else:
            current_value = 0
        if current_value < target_value:
            buy += target_value - current_value
            asset_list.append(asset)
            value_list.append(target_value - current_value)
    return pd.DataFrame({"Asset": asset_list, "Investment Action": value_list}).round(2)
