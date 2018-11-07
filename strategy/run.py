import pandas
import matplotlib.pyplot as plt
import pyfolio as pf
from datetime import datetime
from collections import Counter
from strategy import logger
from strategy.replay import ReplayMany
from strategy.riskmodel import RiskModel

replays = list(ReplayMany().symbols(lambda x: x.endswith('BTC_USDT')))
skip = {'20180103', '20180106', '20180108', '20180121', '20180126', '20180131', '20180203', '20180205',
        '20180206', '20180209', '20180214', '20180310', '20180311', '20180626', '20180627', '20180704'}
risk = RiskModel()

raw_spot_pnl = []
raw_index_pnl = []
raw_index_w1 = []
raw_bt_pnl = []
raw_bt_count = Counter()


def main(algo):
    raw_spot_pnl.clear()
    raw_index_pnl.clear()
    raw_index_w1.clear()
    raw_bt_pnl.clear()

    for r in replays:
        if r.source.partition('_')[-1] not in skip:
            key = datetime.strptime(r.source, 'quotes_%Y%m%d')
            logger.debug('processing {}'.format(r.source))
            px = r.select_field('bar_mean2').groupby(level=0, axis=1).mean()
            px = px.div([v[v.first_valid_index()] for _, v in px.items()], axis=1)
            pnl = px.diff()
            raw_spot_pnl.append(pnl)
            if raw_index_w1:
                w1 = raw_index_w1[-1]
                ipnl = pnl.mul(w1, axis=1)
                raw_index_pnl.append(ipnl)
            raw_index_w1.append(risk.set_pnl(pnl).risk_parity().w1.rename(key))
            algo.set_data(px).run()
            raw_bt_pnl.append(algo.pnl)
            raw_bt_count[key] = algo.trade_count()


if __name__ == '__main__':
    # from strategy.model import SimpleTrend
    #
    # trend = SimpleTrend(window=30, shift=1, fee=0.0001)
    # main(trend)

    # id_spot = pandas.concat(raw_spot_pnl)
    # id_index = pandas.concat(raw_index_pnl)
    # id_trend = pandas.concat(raw_bt_pnl)

    # trade_count = pandas.Series(raw_bt_count)
    # daily_w1 = pandas.DataFrame(raw_index_w1)
    # rolling_w1 = daily_w1.rolling(20).mean()
    # daily_spot = pandas.DataFrame([i.sum().rename(i.index[0].date()) for i in raw_spot_pnl])
    # daily_index = pandas.DataFrame([i.sum().rename(i.index[0].date()) for i in raw_index_pnl])
    # daily_trend = pandas.DataFrame([i.sum().rename(i.index[0]) for i in raw_bt_pnl])
    #
    # agg_trend = daily_trend.mul(daily_w1.shift(1).fillna(1 / daily_w1.shape[1])).sum(axis=1)
    # print(pandas.Series({'ret': agg_trend.mean() * 260,
    #                      'vol': agg_trend.std() * (260 ** 0.5),
    #                      'sharpe': agg_trend.mean() / agg_trend.std() * (260 ** 0.5),
    #                      'neg_days': len(agg_trend[agg_trend < 0]),
    #                      'total_days': len(agg_trend),
    #                      'mdd': (1 - agg_trend.cumsum().div(agg_trend.cumsum().cummax())).max(),
    #                      'daily_trade_count': trade_count.mean()}))
    # agg_trend.cumsum().plot()
    with open('pickle', 'rb') as f:
        import pickle
        agg_trend = pickle.load(f)
    retu = (agg_trend.cumsum()/50+1).pct_change()
    fig = pf.create_returns_tear_sheet(retu, return_fig=True)
    fig.savefig('/Users/sweetdreams/code/fintend/alpha/alpha.png')
    plt.show()

import ccxt
d = ccxt.deribit().fetch_ohlcv