# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/26'

import os
import datetime
from abc import ABCMeta, abstractmethod
from copy import deepcopy
from typing import List, Dict

from backtesting.models import SignalEvent, FillEvent, get_current_event_queue, MarketEvent
from backtesting.performance import create_drawdowns, create_sharpe_ratio
from backtesting import BACKTESTING_ROOT

import pandas as pd
import pyfolio as pf


class Holdings:
    def __init__(self, timestamp, cash, total, fee):
        self.timestamp = timestamp
        self.cash = cash
        self.total = total
        self.fee = fee

    def to_dict(self):
        return {
            'datetime': datetime.datetime.fromtimestamp(self.timestamp),
            'cash': self.cash,
            'total': self.total,
            'fee': self.fee,
        }


class BasePortfolio(metaclass=ABCMeta):
    def __init__(self, *, current_positions: Dict):
        self._current_positions = current_positions
        self.start_timestamp = None
        self.event_queue = get_current_event_queue()
        self.total_assets = None
        self.current_holdings = None
        self.all_holdings = []

    def recieve_event(self, event):
        assert self.start_timestamp, 'must set_start_timestamp first'

        if event.type == SignalEvent.type:
            orders = self.recieve_signal(event)
            for o in orders:
                self.event_queue.put(o)
        elif event.type == MarketEvent.type:
            self.current_holdings = self.get_current_holdings(event)
            self.all_holdings.append(self.current_holdings)
        elif event.type == FillEvent.type:
            self.update_position(event)
            self.update_holdings(event)
        else:
            raise ValueError('Not support event type')

    def set_start_timestamp(self, timestamp):
        self.start_timestamp = timestamp

    def get_position(self):
        return deepcopy(self._current_positions)

    @abstractmethod
    def get_current_holdings(self, event: MarketEvent) -> Holdings:
        pass

    @abstractmethod
    def recieve_signal(self, event: SignalEvent):
        return []

    @abstractmethod
    def update_position(self, event: FillEvent):
        pass

    @abstractmethod
    def update_holdings(self, event: FillEvent):
        pass

    @staticmethod
    def trans_symbol(symbol):
        return symbol.split('/')

    def output_summary_stats(self):
        """
        Creates a list of summary statistics for the portfolio such
        as Sharpe Ratio and drawdown information.
        """
        equity_curve = self.get_equity_curve_dataframe()
        total_return = equity_curve['equity_curve'][-1]
        returns = equity_curve['returns']
        pnl = equity_curve['equity_curve']

        sharpe_ratio = create_sharpe_ratio(returns)
        max_dd, dd_duration = create_drawdowns(pnl)

        import warnings
        warnings.filterwarnings('ignore')
        pf.create_returns_tear_sheet(equity_curve['returns'])
        return

    def get_equity_curve_dataframe(self):
        """
        Creates a pandas DataFrame from the all_holdings
        list of dictionaries.
        """
        curve = pd.DataFrame([h.to_dict() for h in self.all_holdings])
        curve.set_index('datetime', inplace=True)
        curve.index = pd.to_datetime(curve.index)
        curve['returns'] = curve['total'].pct_change()
        curve['equity_curve'] = (1.0+curve['returns']).cumprod()
        return curve


class CCXTBasePortfolio(BasePortfolio):
    def __init__(self, *, current_positions, equity_base):
        self.equity_base = equity_base
        super().__init__(current_positions=current_positions)

    def update_position(self, event: FillEvent):
        coin, money = self.trans_symbol(event.symbol)
        if event.direction == FillEvent.DIRECTION_BUY:
            self._current_positions[event.exchange][money] -= event.price*event.amount
            self._current_positions[event.exchange][coin] += event.amount - event.fee
        elif event.direction == FillEvent.DIRECTION_SELL:
            self._current_positions[event.exchange][money] += event.price*event.amount - event.fee
            self._current_positions[event.exchange][coin] -= event.amount
        else:
            raise ValueError('not supprot direction')

    def get_current_holdings(self, event: MarketEvent):
        fee = self.current_holdings.fee if self.current_holdings else 0
        cash = 0
        total = 0
        coin_price = {}
        for e, v in event.payload.items():
            for s, p in v.items():
                coin, money = self.trans_symbol(s)
                if money == self.equity_base:
                    coin_price[coin] = p[4]

        for e, v in self._current_positions.items():
            for c, a in v.items():
                if c == self.equity_base:
                    cash += a
                else:
                    total += coin_price[c] * a
        total += cash
        return Holdings(event.timestamp, cash, total, fee)

    def update_holdings(self, event: FillEvent):
        pass
        # TODO complete update_holdings

    @abstractmethod
    def recieve_signal(self, event):
        pass
