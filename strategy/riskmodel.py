import copy
import pandas
from scipy.optimize import minimize
from strategy import logger

np = pandas.np


def ann_factor(freq):
    if isinstance(freq, pandas.offsets.Week):
        return 52 / freq.n
    elif isinstance(freq, pandas.offsets.MonthOffset):
        return 12 / freq.n
    elif isinstance(freq, pandas.offsets.QuarterOffset):
        return 4 / freq.n
    elif isinstance(freq, pandas.offsets.YearOffset):
        return freq.n
    return 260 / getattr(freq, 'n', 1)


def sum_to_one(w):
    return 1 - w.sum()


def all_positive(w):
    return w


con_sum_to_one = {'type': 'eq', 'fun': sum_to_one}
con_all_positive = {'type': 'ineq', 'fun': all_positive}
DEFAULT_SETTINGS = {'constraints': [con_sum_to_one, con_all_positive]}


class RiskModel:
    def __init__(self):
        self._pnl = self._cov = None
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.results = {}

    def reset_to_default_settings(self):
        self.settings = copy.deepcopy(DEFAULT_SETTINGS)
        self.results.clear()

    @property
    def freq(self):
        return self.settings.get('freq')

    @freq.setter
    def freq(self, v):
        assert isinstance(v, str)
        assert v[-1].lower() in 'dwmqy'
        try:
            int(v[:-1])
        except ValueError:
            raise ValueError('invalid freq')
        self.settings['freq'] = v

    def set_freq(self, v):
        self.freq = v
        return self

    @property
    def pnl(self):
        if isinstance(self._pnl, pandas.DataFrame):
            if self.freq:
                return self._pnl.add(1).cumprod().asfreq(self.freq, method='ffill').pct_change()
            return self._pnl

    @pnl.setter
    def pnl(self, v):
        assert isinstance(v, pandas.DataFrame)
        assert isinstance(v.index, pandas.DatetimeIndex)
        self._cov = None
        self._pnl = v

    def set_pnl(self, pnl):
        self.pnl = pnl
        return self

    @property
    def cov(self):
        if self._cov is None:
            pnl = self.pnl
            if pnl is not None:
                return pnl.cov()
        return self._cov

    @cov.setter
    def cov(self, v):
        assert isinstance(v, pandas.DataFrame)
        assert v.shape[0] == v.shape[1]
        self._cov = v

    def set_cov(self, v):
        self.cov = v
        return self

    def set_constraints(self, v):
        assert isinstance(v, (dict, list, tuple))
        if isinstance(v, dict):
            v = [v]
        self.settings['constraints'] = v
        return self

    def add_constraints(self, v):
        assert isinstance(v, (dict, list, tuple))
        if isinstance(v, dict):
            v = [v]
        try:
            self.settings['constraints'].extend(v)
        except KeyError:
            self.settings['constraints'] = v
        return self

    def risk_parity(self, **kwargs):
        cov_df = self.cov
        if cov_df is None:
            raise ValueError('cov not set')
        cov_df = cov_df.dropna(how='all').dropna(how='all', axis=1)
        cov = cov_df.values
        n = len(cov)
        w0 = np.ones(n) / n

        def opt(w):
            cw = np.dot(cov, w)
            s = np.dot(w, cw)
            return ((w - s / cw / n) ** 2).sum()

        kwargs.setdefault('constraints', self.settings.get('constraints', ()))

        self.results['res'] = res = minimize(opt, w0, **kwargs)
        if not res.success:
            logger.warning(res.message)
        self.results['w1'] = pandas.Series(res.x, cov_df.columns, name='w1')
        return self

    def risk_budgeting(self, rb, **kwargs):
        cov_df = self.cov
        if cov_df is None:
            raise ValueError('cov not set')
        cov_df = cov_df.dropna(how='all').dropna(how='all', axis=1)
        cov = cov_df.values
        n = len(cov)
        w0 = np.ones(n) / n

        def opt(w):
            cw = np.dot(cov, w)
            s = np.dot(w, cw)
            return ((rb - s / cw / n) ** 2).sum()

        kwargs.setdefault('constraints', self.settings.get('constraints', ()))

        self.results['res'] = res = minimize(opt, w0, **kwargs)
        if not res.success:
            logger.warning(res.message)
        self.results['w1'] = pandas.Series(res.x, cov_df.columns, name='w1')
        return self

    @property
    def w1(self):
        if 'w1' not in self.results:
            self.risk_parity()
        return self.results['w1']

    @property
    def corr(self):
        pnl = self.pnl
        if pnl is not None:
            return pnl.corr()

    def attributions(self, apply_w1=False):
        pnl = self.pnl
        if pnl is not None:
            n = ann_factor(pnl.index.freq)
            if apply_w1:
                return pnl.mul(self.w1, axis=1).std().mul(n ** 0.5)
            return pnl.std().mul(n ** 0.5)


if __name__ == '__main__':
    pass
