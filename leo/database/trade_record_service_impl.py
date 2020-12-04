# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-11-03
@last modified time:2020-11-03
"""


def select(engine, backtesting_id):
    """

    :param engine:
    :param backtesting_id:
    :return:
    """
    sql = 'SELECT backtesting_id,ticker,trade_time,trade_type,price from trade_record where backtesting_id="{}" order by trade_time asc'.format(
        backtesting_id)
    rs_set = engine.execute(sql)
    rs = []
    for row in rs_set:
        rs.append(list(row))
    return rs


def insert_on_duplicate_update(engine, data):
    """

    :param engine:
    :param data:
    :return:
    """
    sql = 'insert into trade_record(backtesting_id,ticker,trade_time,trade_type,price)' \
          ' values (%s,%s,%s,%s,%s)' \
          ' on duplicate key update backtesting_id=values(backtesting_id),ticker=values(ticker),trade_time=values(trade_time),trade_type=values(trade_type),price=values(price)'
    return engine.execute(sql, data)
