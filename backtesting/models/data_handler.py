# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/26'


import threading
import time
import datetime
import traceback
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from typing import List
from abc import ABCMeta, abstractmethod

import ccxt

from backtesting.models import get_current_event_queue, MarketEvent, MarketStopEvent
from backtesting.connections import get_mysql_conn
from backtesting import get_logger


class BaseDataHandler(metaclass=ABCMeta):
    def __init__(self):
        self.event_queue = get_current_event_queue()
        self.payload = None
        self._market_generator = self.market_generator()

    @abstractmethod
    def market_generator(self):
        """
        yield timestamp, data
        :return:
        """
        pass

    def send_market_event(self):
        for t, m in self._market_generator:
            self.payload = m
            self.event_queue.put(MarketEvent(m, t))
            return
        self.send_stop_event()

    def send_stop_event(self):
        self.event_queue.put(MarketStopEvent)


class MysqlCandlesHandler(BaseDataHandler):
    def market_generator(self):
        conn = get_mysql_conn()
        table_name = 'huobipro_EOS_BTC_candle_1m'
        sql = 'select * from {}'.format(table_name)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                while True:
                    line = cursor.fetchone()
                    if not line:
                        return
                    yield line[1:]
        finally:
            conn.close()


class CCXTDataHandler(BaseDataHandler):
    def __init__(self, *, exchanges: List[str], symbols, start, end, dataframe):
        self.exchanges = [getattr(ccxt, e_name)() for e_name in exchanges]
        for e in self.exchanges:
            e.enableRateLimit = True
            e.rateLimit = e.rateLimit * 2
        self.symbols = symbols
        self.startime = int(start * 1000)  # timestamp_ms
        self.endtime = int(end * 1000)  # timestamp_ms
        self.dataframe = dataframe
        self.pool = ThreadPoolExecutor(max_workers=100)
        self.logger = get_logger('data_handler')
        super().__init__()

    def market_generator(self):
        candles = {e.id: {s: None for s in self.symbols} for e in self.exchanges}

        now = self.startime
        while now <= self.endtime:
            futures = {e.id: {s: self.pool.submit(self.fetch_ohlcv, e, s, now)
                              for s in self.symbols} for e in self.exchanges}
            for e, v in futures.items():
                for s, v2 in v.items():
                    futures[e][s] = v2.result()

            while True:
                try:
                    _now = None
                    for e in self.exchanges:
                        for s in self.symbols:
                            candle = futures[e.id][s].pop(0)
                            if not _now:
                                _now = candle[0]
                            else:
                                if _now != candle[0]:
                                    candle[0] = _now
                                    futures[e.id][s].insert(0, candle)
                            candles[e.id][s] = candle
                except IndexError:
                    break
                except AssertionError:
                    raise

                now = _now
                if now <= self.endtime:
                    results = deepcopy(candles)
                    yield (int(now/1000), results)
                else:
                    break
            now = int(60*1000 + now)

    def fetch_ohlcv(self, exchange: ccxt.Exchange, symbol, since):
        while True:
            try:
                candles = exchange.fetch_ohlcv(symbol, self.dataframe, since=since, limit=60*12)
                return candles
            except (ccxt.errors.DDoSProtection, ccxt.errors.RequestTimeout) as e:
                self.logger.debug(error_class=e.__class__.__name__, exchange=exchange.id)
                time.sleep(3)
            except ccxt.errors.BaseError as e:
                self.logger.debug(error_class=e.__class__.__name__)
                self.logger.exception()
                time.sleep(5)


if __name__ == '__main__':
    # dh = MysqlCandlesHandler()
    # while True:
    #     dh.send_market_event()
    #     print(dh.payload)
    #     if dh.event_queue.get().type == MarketStopEvent.type:
    #         break

    dh = CCXTDataHandler(
        exchanges=['bitfinex', 'binance'],
        symbols=['BTC/USDT', 'ETH/BTC'],
        start=datetime.datetime(year=2018, month=6, day=9).timestamp(),
        end=datetime.datetime(year=2018, month=6, day=10).timestamp(),
        dataframe='1m'
    )

    while True:
        dh.send_market_event()
        print(dh.payload)
        if dh.event_queue.get().type == MarketStopEvent.type:
            break
