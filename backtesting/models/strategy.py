# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/26'

from typing import List
from abc import ABCMeta, abstractmethod

from backtesting.models import get_current_event_queue, MarketEvent, BaseDataHandler, SignalEvent


class BaseStrategy(metaclass=ABCMeta):
    def __init__(self):
        self.event_queue = get_current_event_queue()
        self.history_market_length = 60
        self.history_market = []
        self.bars = None

    def recieve_market_event(self, event: MarketEvent):
        assert event.type == MarketEvent.type
        signal_events = self.calculate_signal_event(event.payload)
        for e in signal_events:
            e.set_timestamp(event.timestamp)
            self.event_queue.put(e)
        self.history_market.append(event.payload)
        if len(self.history_market) > self.history_market_length:
            self.history_market.pop(0)

    @abstractmethod
    def calculate_signal_event(self, payload) -> List[SignalEvent]:
        pass
