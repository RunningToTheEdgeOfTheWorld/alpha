# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/27'


import datetime
from backtesting.models import BaseStrategy, CCXTBasePortfolio
from backtesting.models import SignalEvent, OrderEvent
from backtesting.backtesting_engine import CCXTBacktestingEngine


class MyStrategy(BaseStrategy):
    def calculate_signal_event(self, payload):
        """
        生成策略信号
        :param payload: {"exchange":{"symbol": candle}}
        candle = [
                1504541580000, // UTC timestamp in milliseconds, integer
                4235.4,        // (O)pen price, float
                4240.6,        // (H)ighest price, float
                4230.0,        // (L)owest price, float
                4230.7,        // (C)losing price, float
                37.72941911    // (V)olume (in terms of the base currency), float
            ]
        :return:
        """
        signals = []
        import random
        if random.random() > 3:
            signals.append(
                SignalEvent(
                    exchange='binance',
                    symbol='BTC/USDT',
                    direction='long',  # or short
                    payload=payload,
                )
            )

        return signals


class MyProtfolio(CCXTBasePortfolio):
    def recieve_signal(self, event: SignalEvent):
        """
        接收信号调整仓位
        :param event:
        :return:
        """
        orders = []

        position = self.get_position()  # {"exchange": {"coin": 100}}
        coin, money = self.trans_symbol(event.symbol)  # BTC/USDT coin=BTC, money=USDT
        if event.direction == 'long':
            orders.append(
                OrderEvent(
                    exchange=event.exchange,
                    symbol=event.symbol,
                    order_type='limit',
                    direction='buy',  # or sell
                    amount=1,
                    price=event.payload[event.exchange][event.symbol][4]
                )
            )
        if event.direction == 'short':
            orders.append(
                OrderEvent(
                    exchange=event.exchange,
                    symbol=event.symbol,
                    order_type='limit',
                    direction='sell',  # or sell
                    amount=1,
                    price=event.payload[event.exchange][event.symbol][4]
                )
            )
        return orders


if __name__ == '__main__':
    strategy = MyStrategy()
    portfolio = MyProtfolio(
        current_positions={
            'bitfinex': {'BTC': 1, 'ETH': 0, 'USDT': 100000},
            'binance': {'BTC': 0, 'ETH': 0, 'USDT': 100000},
        },
        equity_base='USDT',
    )
    engine = CCXTBacktestingEngine(
        exchanges=['bitfinex', 'binance'],
        symbols=['BTC/USDT', 'ETH/USDT'],
        start=datetime.datetime(year=2018, month=10, day=1).timestamp(),
        end=datetime.datetime(year=2018, month=11, day=5).timestamp(),
        dataframe='1m',
        strategy=strategy,
        portfolio=portfolio,
    )
    engine.run_until_complete()
