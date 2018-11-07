# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/28'

import numpy as np
import pandas as pd


def create_sharpe_ratio(returns, periods=252):
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)


def create_drawdowns(equity_curve):
    # Calculate the cumulative returns curve
    # and set up the High Water Mark
    # Then create the drawdown and duration series
    hwm = [0]
    eq_idx = equity_curve.index
    drawdown = pd.Series(index=eq_idx)
    duration = pd.Series(index=eq_idx)

    # Loop over the index range
    for t in range(1, len(eq_idx)):
        cur_hwm = max(hwm[t-1], equity_curve[t])
        hwm.append(cur_hwm)
        drawdown[t] = hwm[t] - equity_curve[t]
        duration[t] = 0 if drawdown[t] == 0 else duration[t-1] + 1
    return drawdown.max(), duration.max()

