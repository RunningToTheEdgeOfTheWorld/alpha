# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/26'

import queue
import datetime
from abc import ABCMeta, abstractmethod, abstractproperty

from backtesting import errors


class BaseEventQueue(metaclass=ABCMeta):
    @abstractmethod
    def get(self):
        pass

    @abstractmethod
    def put(self, v):
        pass

    @abstractmethod
    def qsize(self):
        pass


class EventQueue(BaseEventQueue):
    def __init__(self):
        self.queue = queue.Queue()

    def get(self):
        try:
            return self.queue.get(block=False)
        except queue.Empty:
            raise errors.EventEmpty()

    def put(self, v):
        return self.queue.put(v)

    def qsize(self):
        return self.queue.qsize()


default_event_queue = EventQueue()


def get_current_event_queue():
    return default_event_queue


class BaseEvent(metaclass=ABCMeta):
    @property
    @abstractmethod
    def type(self):
        pass


class MarketEvent(BaseEvent):
    type = 'MARKET'

    def __init__(self, payload, timestamp):
        self.payload = payload
        datetime.datetime.fromtimestamp(timestamp)
        self.timestamp = timestamp


class MarketStopEvent(BaseEvent):
    type = 'MARKET_STOP'


class SignalEvent(BaseEvent):
    type = 'SIGNAL'
    DIRECTION_LONG = 'long'
    DIRECTION_SHORT = 'short'

    def __init__(self, *, exchange: str, symbol, direction, payload, **extra):
        self.exchange = exchange
        self.symbol = symbol
        assert direction in (self.DIRECTION_LONG, self.DIRECTION_SHORT)
        self.direction = direction
        self.payload = payload
        self.timestamp = None
        self.extra = extra

    def set_timestamp(self, timestamp):
        datetime.datetime.fromtimestamp(timestamp)
        self.timestamp = timestamp


class OrderEvent(BaseEvent):
    type = 'ORDER'
    DIRECTION_BUY = 'buy'
    DIRECTION_SELL = 'sell'

    def __init__(self, *, exchange: str, symbol, order_type, direction, amount, price=None):
        self.exchange = exchange
        self.symbol = symbol
        self.order_type = order_type
        self.amount = amount
        self.price = price
        assert direction in (self.DIRECTION_BUY, self.DIRECTION_SELL)
        self.direction = direction


class FillEvent(BaseEvent):
    type = 'FILL'
    DIRECTION_BUY = 'buy'
    DIRECTION_SELL = 'sell'

    def __init__(self, *, exchange: str, symbol, price, amount, direction, fee):
        self.exchange = exchange
        self.symbol = symbol
        self.price = price
        self.amount = amount
        assert direction in (self.DIRECTION_BUY, self.DIRECTION_SELL)
        self.direction = direction
        self.fee = fee
