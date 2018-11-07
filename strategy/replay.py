import pandas
from datetime import datetime
from collections import namedtuple, defaultdict, OrderedDict as od
from strategy import sql, tables


class Bar(namedtuple('bar', 'pid, exchange, symbol, timestamp_ms, o_price, h_price, l_price, c_price, volume')):
    @property
    def timestamp(self):
        return datetime.fromtimestamp(self.timestamp_ms / 1e3)

    @property
    def mkt_value(self):
        return self.c_price * self.volume

    @property
    def bar_range(self):
        return 2 * (self.h_price - self.l_price) / (self.o_price + self.c_price)

    @property
    def bar_mean2(self):
        return (self.o_price + self.c_price) / 2

    @property
    def bar_mean4(self):
        return (self.o_price + self.h_price + self.l_price + self.c_price) / 4


class _Replay:
    def __init__(self):
        self.sources = sorted([i for i in tables if i.startswith('quotes_')])
        self.exchange_filter = self.symbol_filter = None

    def exchanges(self, by):
        if by is not None and not callable(by):
            raise TypeError
        self.exchange_filter = by
        return self

    def symbols(self, by):
        if by is not None and not callable(by):
            raise TypeError
        self.symbol_filter = by
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.exchange_filter = self.symbol_filter = None


class Replay(_Replay):
    def __init__(self, source):
        super().__init__()
        if source not in self.sources:
            raise ValueError
        self.source = source
        self.last_price = {}

    def __iter__(self):
        cursor = sql.execute('select * from {} order by timestamp_ms'.format(self.source))
        for pid, exch, sym, ts, o, h, l, c, v in cursor:
            self.last_price[sym] = bar = Bar(pid, exch, sym, ts, o, h, l, c, v)
            if callable(self.symbol_filter) and not self.symbol_filter(sym):
                continue
            if callable(self.exchange_filter) and not self.exchange_filter(exch):
                continue
            yield bar

    def all_exchange(self):
        c = sql.execute('select exchange from {}'.format(self.source))
        return set(i[0] for i in c)

    def all_symbol(self):
        c = sql.execute('select symbol from {}'.format(self.source))
        return set(i[0] for i in c)

    def select_field(self, field):
        res = defaultdict(od)
        for bar in self:
            res[(bar.symbol, bar.exchange)][bar.timestamp] = getattr(bar, field)

        return pandas.DataFrame(res)

    def to_frame(self):
        return pandas.DataFrame([bar._asdict() for bar in self])


class ReplayMany(_Replay):
    def __iter__(self):
        for source in self.sources:
            yield Replay(source).symbols(self.symbol_filter).exchanges(self.exchange_filter)


if __name__ == '__main__':
    pass
