# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-12-01
@last modified time:2020-12-01
"""
from leo.database.joinquant_record import *
from datetime import datetime


def select(session, strategy_id, start_time=None):
    return session.query(OrderRecord).filter(and_(OrderRecord.strategy_id == strategy_id,
                                                  OrderRecord.execute_time >= start_time,
                                                  OrderRecord.status == 0)).all()


def insert(session, strategy_id, ticker, execute_time, order_side, amount, order_type=0, price=0):
    """

    :param session:
    :param strategy_id:
    :param ticker:
    :param execute_time:
    :param order_side: -1:short 1:long
    :param amount:
    :param order_type: 0:market 1:limit
    :param price:
    :return:
    """
    record = OrderRecord(strategy_id=strategy_id, execute_time=execute_time, ticker=ticker, order_side=order_side,
                         amount=amount, order_type=order_type, price=price, create_time=datetime.now(), status=0)
    session.add(record)
    session.commit()


if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/join_quant_backtesting?charset=utf8')
    session = sessionmaker(bind=engine)()
    # for i in select(session,0,'2020-12-01'):
    #     i.status=1
    order_record = OrderRecord(strategy_id='1', execute_time='1990-01-01 00:00:00', ticker='000001', order_side=1,
                               amount=100)
    session.add(order_record)
    session.commit()
