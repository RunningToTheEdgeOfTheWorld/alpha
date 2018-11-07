# alpha -- 量化回测框架和量化策略

## 回测框架
### 使用
* 回测框架分为以下几个部分：
    1. data_handler 负责数据接入
    目前支持coinpool的influxdb的数据源和ccxt的网络数据源
    2. strategy 负责根据策略发出买卖指令
    3. portfolio 负责根据买卖指令调整仓位，发出订单信号
    4. execition负责下单并且监听回掉信号
   
## 回测框架使用说明：
首先导入回测引擎模块：
        
    from backtesting.backtesting_engine import CCXTBacktestingEngine
    
导入strategy和portfolio模块：
    from backtesting.models import BaseStrategy, CCXTBasePortfolio
    
重写策略和回测模块的方法

    class MyStrategy(BaseStrategy):
        def calculate_signal_event(self, payload):
            pass
        
    class MyProtfolio(CCXTBasePortfolio):
        def recieve_signal(self, event: SignalEvent):
            pass
            
给回测引擎传入参数启动回测：

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
    
示例代码见examples文件夹下
