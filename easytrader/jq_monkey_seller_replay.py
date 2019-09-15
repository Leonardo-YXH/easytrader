# coding:utf-8
import jqsdk
import jqdata
from jqlib.technical_analysis import *
from assistant import money_flow_statistic
import pandas as pd
from jqtalib import talib_real


##### 下面是策略代码编辑部分 #####

def initialize(context):
    set_benchmark('000300.XSHG')
    set_option('use_real_price', True)
    log.info('initialize run only once')
    ### 股票相关设定 ###
    # 股票类每笔交易时的手续费是：买入时佣金万分之三，卖出时佣金万分之三加千分之一印花税, 每笔交易佣金最低扣5块钱
    set_order_cost(OrderCost(close_tax=0.001, open_commission=0.0003, close_commission=0.0003, min_commission=5),
                   type='stock')

    g.code = '000001.XSHE'
    # g.real_bar=talib_real.VMA_Real(g.code,M1=5,M2=10,M_HIGH=1,M_LOW=1,M_OPEN=0,M_CLOSE=3)
    g.real_bar=talib_real.KD_Real(g.code,N=5,M1=3,M2=3)

    g.ready_to_buy=True
    g.monkey_seller=None
    # run_daily(market_open, time='open', reference_security='000300.XSHG')


def before_trading_start(context):
    g.real_bar.before_market_open(context)

    if g.monkey_seller is not None:
        g.monkey_seller.update_prediction_data_before_market_backtest()

def after_trading_end(context):
    g.real_bar.after_market_close(context)

    if not g.ready_to_buy:
        orders = get_orders()
        order_successful=False
        for order in orders.values():
            if order.security == g.code and order.is_buy and order.status in [OrderStatus.filled,OrderStatus.canceled,OrderStatus.rejected,OrderStatus.held] and order.filled>0:
                g.monkey_seller = money_flow_statistic.monkey_seller(g.code, order.price, order.filled,stop_loss=0.04,moving_stop_loss=0.03,
                                                                     is_backtest=True)
                order_successful=True
        if not order_successful:
            g.ready_to_buy=True

    if g.monkey_seller is not None:
        pre_bar = get_price(g.code, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                            fields=['high', 'low', 'close'], skip_paused=True, count=1).iloc[0]
        g.monkey_seller.update_today_data_as_pre_data_after_market_backtest(pre_bar)

def on_strategy_end(context):

    log.info('回测结束')


def handle_data(context, data):
    # log.info(str('函数运行时间(handle_data(context, data)):'+str(context.current_dt)))
    g.real_bar.handle_data(context, data)
    if g.ready_to_buy:
        buy(context,data)
    if g.monkey_seller is not None:
        sell(context,data)



def buy(context,data):
    if g.real_bar.check()>0:
        # 记录这次买入
        log.info(str('买入下单时间:' + str(context.current_dt)))
        # 用所有 cash 买入股票
        order_value(g.code, context.portfolio.available_cash)

        g.ready_to_buy=False


def sell(context,data):
    tick_data=pd.Series({'price':data[g.code].avg,'time':context.current_dt.strftime('%H:%M:%S')})
    if g.monkey_seller.check_sell(tick_data=tick_data):
        # 记录这次卖出
        log.info(str('卖出下单时间:' + str(context.current_dt)))
        # 卖出所有股票,使这只股票的最终持有量为0
        order_target(g.code, 0)
        g.ready_to_buy=True
        g.monkey_seller=None

def run():
    params = {
        'token': '72ca6f67350315c5df5856ef91f2ad3c',
        'algorithmId': 7,
        'baseCapital': 200000,
        'frequency': 'minute',
        'startTime': '2018-01-01',
        'endTime': '2018-09-28',
        'name': "monkey_seller"
    }
    jqsdk.run(params)
##### 下方代码为 IDE 运行必备代码 #####
if __name__ == '__main__':
    run()
