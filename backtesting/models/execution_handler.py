# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/26'


from abc import ABCMeta, abstractmethod

import ccxt

from backtesting.models import OrderEvent, get_exchange, get_current_event_queue, FillEvent


class BaseExecutionHandler(metaclass=ABCMeta):
    def __init__(self):
        self.event_queue = get_current_event_queue()

    @property
    def is_backtesting(self):
        return True

    def recieve_event(self, event: OrderEvent):
        if not self.is_backtesting:
            self.execute_order(event)
        self.send_fill_event(event)

    @abstractmethod
    def execute_order(self, event: OrderEvent):
        pass

    @abstractmethod
    def get_fee(self, event: OrderEvent):
        pass

    def send_fill_event(self, event: OrderEvent):
        fe = FillEvent(
            exchange=event.exchange,
            symbol=event.symbol,
            price=event.price,
            direction=event.direction,
            amount=event.amount,
            fee=self.get_fee(event),
        )
        self.event_queue.put(fe)


class CCXTExecution(BaseExecutionHandler):
    def execute_order(self, event: OrderEvent):
        exchange = get_exchange(event.exchange)
        exchange.create_order(
            symbol=event.symbol,
            order_type=event.order_type,
            direction=event.direction,
            amount=event.amount,
            price=event.price,
        )

    def get_fee(self, event: OrderEvent):
        if event.direction == OrderEvent.DIRECTION_BUY:
            return 0.002 * event.amount
        if event.direction == OrderEvent.DIRECTION_SELL:
            return 0.002 * event.amount * event.price

