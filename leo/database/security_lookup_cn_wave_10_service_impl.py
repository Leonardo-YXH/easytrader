# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-17
@last modified time:2020-09-17
"""


def insert_on_duplicate_update(engine, data):
    """

    :param engine:
    :param data:
    :return:
    """
    sql = 'insert into security_lookup_cn_wave_10(ticker,time_x,price,adj_factor)' \
          ' values (%s,%s,%s,%s)' \
          ' on duplicate key update ticker=values(ticker),time_x=values(time_x),price=values(price),adj_factor=values(adj_factor)'
    return engine.execute(sql, data)


def update(engine, ticker, pre_time_x, time_x, price, adj_factor):
    """

    :param engine:
    :param ticker:
    :param pre_time_x:
    :param time_x:
    :param price:
    :param adj_factor:
    :return:
    """
    sql = 'update security_lookup_cn_wave_10 set time_x="{}",price={},adj_factor={} where ticker="{}" and time_x="{}"'.format(
        time_x, price, adj_factor, ticker, pre_time_x)
    return engine.execute(sql)


def select_latest(engine, ticker, time_x):
    """
    获取离time_x最近的一个
    :param engine:
    :param ticker:
    :param time_x:
    :return:
    """
    sql = 'select price,adj_factor from security_lookup_cn_wave_10 where ticker="{}" and time_x<="{}" ORDER BY time_x desc limit 1'.format(
        ticker, time_x)
    rs_set = engine.execute(sql)
    price = None
    adj_factor = None
    for p, f in rs_set:
        price = p
        adj_factor = f

    return price, adj_factor


def select_from_to_now(engine, ticker, time_x):
    """

    :param engine:
    :param ticker:
    :param time_x:
    :return:
    """
    sql = 'select time_x,DATE_FORMAT(time_x,"%%Y%%m%%d") as trade_date,price from security_lookup_cn_wave_10 where ticker="{}" and time_x>="{}" ORDER BY time_x desc'.format(
        ticker, time_x)
    rs_set = engine.execute(sql)
    waves = []
    for row in rs_set:
        waves.append(list(row))

    return waves


def delete_from_time(engine, ticker, time_x):
    """
    删除time_x之后的数据
    :param engine:
    :param ticker:
    :param time_x:
    :return:
    """
    sql = 'delete from security_lookup_cn_wave_10 where ticker="{}" and time_x>"{}"'.format(ticker, time_x)
    return engine.execute(sql)
