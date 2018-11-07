# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/27'

from abc import ABCMeta, abstractmethod

import ccxt


class BaseExchange(metaclass=ABCMeta):
    @abstractmethod
    def create_order(self, *, symbol, order_type, direction, amount, price):
        pass


class CCXTExchange(BaseExchange):
    ORDER_TYPE_LIMIT = 'limit'
    ORDER_TYPE_MARKET = 'market'

    def __init__(self, exchange_id, *args, **kwargs):
        self.ccxt_exchange = getattr(ccxt, exchange_id)(*args, **kwargs)
        self.ccxt_exchange.enableRateLimit = True
        self.ccxt_exchange.rateLimit = self.ccxt_exchange.rateLimit * 1.5
        self.name = self.ccxt_exchange.id

    def create_order(self, *, symbol, order_type, direction, amount, price):
        from backtesting.models import OrderEvent
        if order_type == self.ORDER_TYPE_LIMIT:
            if direction == OrderEvent.DIRECTION_BUY:
                return self.ccxt_exchange.create_limit_buy_order(symbol, amount, price)
            elif direction == OrderEvent.DIRECTION_SELL:
                return self.ccxt_exchange.create_limit_sell_order(symbol, amount, price)
            else:
                raise ValueError('Not support order direction')

        elif order_type == self.ORDER_TYPE_MARKET:
            if direction == OrderEvent.DIRECTION_BUY:
                return self.ccxt_exchange.create_market_buy_order(symbol, amount)
            elif direction == OrderEvent.DIRECTION_SELL:
                return self.ccxt_exchange.create_market_sell_order(symbol, amount)
            else:
                raise ValueError('Not support order direction')

        else:
            raise ValueError('Not support order type')


g_exchange = {}


def get_exchange(exchange_name):
    global g_exchange
    exc = g_exchange.get(exchange_name)
    if not exc:
        exc = CCXTExchange(exchange_name)
        g_exchange[exchange_name] = exc
    return exc
