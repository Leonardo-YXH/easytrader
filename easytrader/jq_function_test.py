# coding:utf-8
import jqsdk
import jqdata
from jqlib.technical_analysis import *
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

    g.security = '000001.XSHE'
    # g.macd=talib_real.MACD_Real(g.security,short=12,long=26,mid=9)
    # g.kd=talib_real.KD_Real(g.security,N=5,M1=3,M2=3)
    # g.rsi=talib_real.RSI_Real(g.security,N1=6,N2=12,N3=24)
    # g.roc=talib_real.ROC_Real(g.security,N=12,M=6)
    # g.ma=talib_real.MA_Real(g.security,M1=5,M2=10,M3=20,M4=60)
    # g.cci=talib_real.CCI_Real(g.security,N=14)
    # g.adtm = talib_real.ADTM_Real(g.security, N=23, M=8)
    # g.boll=talib_real.BOLL_Real(g.security,M=20)
    # g.vma = talib_real.VMA_Real(g.security)
    g.real=talib_real.SKDJ_Real(g.security,N=9,M=3)

def before_trading_start(context):
    g.real.before_market_open(context)
    # g.macd.before_market_open(context)
    # g.kd.before_market_open(context)
    # g.rsi.before_market_open(context)
    # g.roc.before_market_open(context)
    # g.ma.before_market_open(context)
    # g.cci.before_market_open(context)
    # g.adtm.before_market_open(context)
    # g.boll.before_market_open(context)
    # g.vma.before_market_open(context)

def after_trading_end(context):
    g.real.after_market_close(context)
    log.info(str(context.current_dt)+'   ' + g.real.to_string())
    rs=g.real.value()
    log.info('k_:' + str(rs['K_']) + '   d_:' + str(rs['D_']))
    # g.macd.after_market_close(context)
    # rs=g.macd.value()
    # log.info(str(context.current_dt) + '  dif:' + str(rs['dif']) + '   dea:' + str(rs['dea']))
    # g.kd.after_market_close(context)
    # rs=g.kd.value()
    # log.info(str(context.current_dt) + '  k:' + str(rs['K']) + '   d:' + str(rs['D']))
    # g.rsi.after_market_close(context)
    # rs = g.rsi.value()
    # log.info(str(context.current_dt) + '  rsi1:' + str(rs['rsi1']) + '   rsi2:' + str(rs['rsi2'])+ '   rsi3:' + str(rs['rsi3']))
    # g.roc.after_market_close(context)
    # rs = g.roc.value()
    # log.info(str(context.current_dt) + '  roc:' + str(rs['roc']) + '   maroc:' + str(rs['maroc']))
    # g.ma.after_market_close(context)
    # rs = g.ma.value()
    # log.info(str(context.current_dt) + '  ma1:' + str(rs['ma1']) + '   ma2:' + str(rs['ma2']) + '   ma3:' + str(rs['ma3']) + '   ma4:' + str(rs['ma4']))
    # g.cci.after_market_close(context)
    # rs = g.cci.value()
    # log.info(str(context.current_dt) + '  cci:' + str(rs['cci']))
    # g.adtm.after_market_close(context)
    # rs = g.adtm.value()
    # log.info(str(context.current_dt) + '  adtm:' + str(rs['adtm']) + '  maadtm:' + str(rs['maadtm']))
    # g.boll.after_market_close(context)
    # rs = g.boll.value()
    # log.info(str(context.current_dt) + '  boll:' + str(rs['boll']) + '  ub:' + str(rs['ub']))
    # g.vma.after_market_close(context)
    # rs = g.vma.value()
    # log.info(str(context.current_dt) + '  ma1:' + str(rs['ma1']) + '  ma2:' + str(rs['ma2']))


def on_strategy_end(context):
    log.info('回测结束')


def handle_data(context, data):
    g.real.handle_data(context,data)
    # log.info(str('函数运行时间(handle_data(context, data)):'+str(context.current_dt)))

    # g.macd.handle_data(context, data)
    # rs=g.macd.value()
    # log.info(str(context.current_dt) + '  dif:' + str(rs['dif']) + '   dea:' + str(rs['dea']))

    # g.kd.handle_data(context,data)
    # rs=g.kd.value()
    # log.info(str(context.current_dt) + '  k:' + str(rs['K']) + '   d:' + str(rs['D']))

    # g.rsi.handle_data(context, data)
    # rs = g.rsi.value()
    # log.info(str(context.current_dt) + '  rsi1:' + str(rs['rsi1']) + '   rsi2:' + str(rs['rsi2'])+ '   rsi3:' + str(rs['rsi3']))

    # g.roc.handle_data(context, data)
    # rs = g.roc.value()
    # if context.current_dt.hour == 14 and context.current_dt.minute == 59:
    #     log.info(str(context.current_dt) + '  roc:' + str(rs['roc']) + '   maroc:' + str(rs['maroc'])+' price:'+str(data[g.security].close))

    # g.ma.handle_data(context,data)
    # g.cci.handle_data(context,data)
    # g.adtm.handle_data(context, data)
    # g.boll.handle_data(context, data)
    # g.vma.handle_data(context, data)


def run():
    params = {
        'token': '72ca6f67350315c5df5856ef91f2ad3c',
        'algorithmId': 8,
        'baseCapital': 100000,
        'frequency': 'minute',
        'startTime': '2018-09-25',
        'endTime': '2018-09-28',
        'name': "unit test"
    }
    jqsdk.run(params)


##### 下方代码为 IDE 运行必备代码 #####
if __name__ == '__main__':
    run()
