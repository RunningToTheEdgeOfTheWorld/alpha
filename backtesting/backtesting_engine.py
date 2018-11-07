# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/25'

from backtesting.models import BaseStrategy, CCXTBasePortfolio, CCXTDataHandler, CCXTExecution
from backtesting.main_loop import Loop


class CCXTBacktestingEngine(Loop):
    def __init__(
        self,
        *,
        exchanges,
        symbols,
        start,
        end,
        dataframe,
        strategy: BaseStrategy,
        portfolio: CCXTBasePortfolio,
    ):
        execution = CCXTExecution()
        data_handler = CCXTDataHandler(
            exchanges=exchanges,
            symbols=symbols,
            start=start,
            end=end,
            dataframe=dataframe,
        )
        portfolio.set_start_timestamp(start)

        coins = set()
        for s in symbols:
            c, m = portfolio.trans_symbol(s)
            coins.add(c)
            coins.add(m)

        assert portfolio.equity_base == 'USDT', 'only support USDT'
        for c in coins:
            if c != portfolio.equity_base:
                check_sym = '{}/{}'.format(c, portfolio.equity_base)
                assert check_sym in symbols, '{} must in symbols'.format(check_sym)

        super().__init__(
            data_handler=data_handler,
            strategy=strategy,
            portfolio=portfolio,
            execution=execution,
        )

