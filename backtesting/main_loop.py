# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/25'

import signal
from pprint import pprint

from backtesting.models import get_current_event_queue
from backtesting.models import BaseDataHandler
from backtesting.models import BaseStrategy
from backtesting.models import BasePortfolio
from backtesting.models import BaseExecutionHandler
from backtesting import get_logger
from backtesting import errors


class Loop:
    def __init__(
            self,
            data_handler: BaseDataHandler,
            strategy: BaseStrategy,
            portfolio: BasePortfolio,
            execution: BaseExecutionHandler,
    ):
        self.event_queue = get_current_event_queue()
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.execution = execution
        self.logger = get_logger('loop')

    def run_until_complete(self):
        from backtesting.models import MarketEvent
        from backtesting.models import SignalEvent
        from backtesting.models import FillEvent
        from backtesting.models import OrderEvent
        from backtesting.models import MarketStopEvent
        self.logger.info(action='loop_start')

        def _exit(*_, **__):
            self.event_queue.put(MarketStopEvent())

        signal.signal(signal.SIGTERM, _exit)
        signal.signal(signal.SIGINT, _exit)

        while True:
            self.data_handler.send_market_event()
            while True:
                try:
                    e = self.event_queue.get()
                except errors.EventEmpty:
                    break
                if e.type == MarketEvent.type:
                    self.strategy.recieve_market_event(e)
                    self.portfolio.recieve_event(e)
                elif e.type == SignalEvent.type:
                    self.portfolio.recieve_event(e)
                elif e.type == FillEvent.type:
                    self.portfolio.recieve_event(e)
                elif e.type == OrderEvent.type:
                    self.execution.recieve_event(e)
                elif e.type == MarketStopEvent.type:
                    self.portfolio.output_summary_stats()
                    raise SystemExit()
                else:
                    raise ValueError('Not support event type')
