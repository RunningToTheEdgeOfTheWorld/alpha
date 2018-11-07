from abc import ABCMeta, abstractmethod
import pandas

np = pandas.np


class BaseModel(metaclass=ABCMeta):
    fee = 0.002

    def __init__(self, **kwargs):
        self._data = self.sig = self._pnl = None
        self.kwargs = kwargs

    @property
    def pnl(self):
        if self._pnl is None:
            self.run()
        return self._pnl

    @pnl.setter
    def pnl(self, v):
        self._pnl = v

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, v):
        if isinstance(v, pandas.Series):
            v = v.to_frame()
        assert isinstance(v, pandas.DataFrame)
        assert isinstance(v.index, pandas.DatetimeIndex)
        self._data = v.dropna(how='all')

    def set_data(self, data):
        self.data = data
        return self

    @abstractmethod
    def run(self):
        pass

    def result(self, agg=False):
        pnl = self.pnl.sum(axis=1) if agg else self.pnl
        return pnl.cumsum()

    def trade_count(self):
        return self.sig.diff().abs().sum().sum()


class SimpleTrend(BaseModel):
    window = 20
    shift = 1

    def run(self):
        data = self.data.ffill()
        window = self.kwargs.get('window', self.window)
        shift = self.kwargs.get('shift', self.shift)
        fee = self.kwargs.get('fee', self.fee)
        self.sig = sig = np.sign(data.sub(data.rolling(window).mean()).fillna(0))
        fees = sig.diff().abs().mul(fee).fillna(0)
        self.pnl = data.diff().mul(sig.shift(shift)).sub(fees).fillna(0)


if __name__ == '__main__':
    pass
