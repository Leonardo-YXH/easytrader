# -*- coding: utf-8 -*-
import sys
sys.path.append('.')
from easytrader import api
from leo.database import order_record_service_impl
from apscheduler.schedulers.background import BackgroundScheduler, BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tushare as ts


def run():
    executors = {
        'default': {'type': 'threadpool', 'max_workers': 10},
        'processpool': ProcessPoolExecutor(max_workers=5)
    }
    scheduler = BlockingScheduler()
    scheduler.configure(executors=executors)


    client = api.use('ths', debug=False)
    client.connect(r"c:\\workspace\\同花顺独立下单final\\\\xiadan.exe", timeout=5)
    client.enable_type_keys_for_editor()
    # add job for computing trendency of all stock
    scheduler.add_job(join_quant_follower_sell, 'cron', day_of_week='mon-fri', hour=9, minute=27,
                      args=[client])
    scheduler.add_job(join_quant_follower_buy, 'cron', day_of_week='mon-fri', hour=9, minute=31, args=[client])
    # join_quant_follower_sell(client,session)
    # join_quant_follower_buy(client,session)
    try:
        scheduler.start()
    except(KeyboardInterrupt, SystemExit):
        scheduler.remove_all_jobs()


def join_quant_follower_sell(client):
    engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/join_quant_backtesting?charset=utf8')
    session = sessionmaker(bind=engine)()
    trade_orders = order_record_service_impl.select(session, strategy_id=110,
                                                    start_time=datetime.now().strftime('%Y-%m-%d'))
    pos = client.position
    pos_dict = {}
    for p in pos:
        pos_dict[p['证券代码']] = p

    for order in trade_orders:
        if order.order_side == -1:
            security = order.ticker[:6]
            if security in pos_dict:
                client.market_sell(security, pos_dict[security]['可用余额'], ttype=get_ttype(security))
                order.status = 1

    session.commit()


def join_quant_follower_buy(client):
    engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/join_quant_backtesting?charset=utf8')
    session = sessionmaker(bind=engine)()
    trade_orders = order_record_service_impl.select(session, strategy_id=110,
                                                    start_time=datetime.now().strftime('%Y-%m-%d'))

    pos = client.position
    pos_dict = {}
    for p in pos:
        pos_dict[p['证券代码']] = p

    balance = client.balance
    available_volume = balance['可用金额']
    long_orders = []
    for order in trade_orders:
        if order.order_side == 1:
            long_orders.append(order)
    if len(long_orders) > 0:
        min_volume = 20000
        max_volume = 100000
        per_amount = available_volume / len(long_orders)
        if per_amount > max_volume:
            per_amount = max_volume
        elif per_amount < min_volume:
            per_amount = min_volume
            long_orders_length = int(available_volume // per_amount)
            long_orders = long_orders[:long_orders_length]

        for order in long_orders:
            security = order.ticker[:6]
            real_quote = ts.get_realtime_quotes(security)
            if not real_quote.empty:
                amount = per_amount // float(real_quote['price'][0])
                amount = amount - amount % 100
                print('ticker:{} amount:{}'.format(security, amount))
                client.market_buy(security, amount, ttype=get_ttype(security))
                order.status = 1

        session.commit()


def get_ttype(ticker):
    if ticker.startswith('60'):
        return u'1-最优五档即时成交剩余转限价申报'
    else:
        return u'1-对手方最优价格申报'


def test():
    # join_quant_follower()
    client = api.use('ths', debug=True)
    # client.connect(r"D:\\同花顺软件\\同花顺\\xiadan.exe", timeout=5)
    # client.connect(r"D:\\software\\同花顺独立下单\\xiadan.exe",timeout=5)
    client.connect(r"c:\\workspace\\同花顺独立下单final\\xiadan.exe", timeout=5)

    client.enable_type_keys_for_editor()
    help_msg = """1--buyF1
    2--sellF2
    3--chedanF3
    4--searchF4:chicang
    5--F4:today:trader
    6--F4:today:entrusts
    """
    print(help_msg)
    msg = input("please input your choice:")
    while True:
        if msg == '1':
            msg = input("limit buy, please input your ticker,price and amount:")
            words = msg.split(' ')
            client.buy(words[0], float(words[1]), amount=int(words[2]))

        elif msg == '1.1':
            msg = input("market buy, please input your ticker and amount:")
            words = msg.split(' ')
            client.market_buy(words[0], amount=int(words[1]), ttype=u'1-对手方最优价格申报')
        elif msg == '2':
            msg = input("limit sell, please input your ticker,price and amount:")
            words = msg.split(' ')
            client.sell(words[0], float(words[1]), amount=int(words[2]))
        elif msg == '2.1':
            msg = input("market sell, please input your ticker and amount:")
            words = msg.split(' ')
            client.market_sell(words[0], amount=int(words[1]), ttype=u'1-对手方最优价格申报')
        elif msg == '3':
            client.cancel_entrust(input('order no:'))
        elif msg == '3.1':
            print(client.cancel_entrusts)
        elif msg == '3.2':
            print(client.cancel_all_entrust())
        elif msg == '3.3':
            print(client.cancel_all_sell_entrust())
        elif msg == '3.4':
            print(client.cancel_all_buy_entrust())
        elif msg == '4':
            print(client.balance)
        elif msg == '4.1':
            pos = client.position
            print(client.position)
        elif msg == '5':
            print(client.today_trades)
        elif msg == '6':
            print(client.today_entrusts)
        elif msg == '7':
            # account_type=input("account type:")
            # account_no=input('account no:')
            print(client.switch_trade_account(u'上海Ａ股', u'A446850006'))
        else:
            break
        print(help_msg)
        msg = input("please input your choice:")


if __name__ == '__main__':
    run()
