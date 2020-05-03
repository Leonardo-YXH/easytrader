# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-04-29
@last modified time:2020-04-29
"""
import sqlalchemy
from datetime import date


def insert_on_duplicate_update(engine, data):
    """
    time_x使用当前时间
    @param engine:
    @param data:
    """
    sql = 'insert into account_holding(account_no,time_x,ticker,name_cn,qty,available_qty,avg_cost,pnl) ' \
          'values (%s,%s,%s,%s,%s,%s,%s,%s)' \
          'on duplicate key update account_no=values(account_no),time_x=values(time_x),ticker=values(ticker),name_cn=values(name_cn),qty=values(qty),available_qty=values(available_qty),avg_cost=values(avg_cost),pnl=values(pnl)'

    return engine.execute(sql, data)


def restore(engine, data):
    time_x = data[0][1]
    account_nos = []
    for item in data:
        account_nos.append(item[0])
    account_nos = set(account_nos)
    for account_no in account_nos:
        delete(engine, account_no, time_x)
    sql = 'insert into account_holding(account_no,time_x,ticker,name_cn,qty,available_qty,avg_cost,pnl) ' \
          'values (%s,%s,%s,%s,%s,%s,%s,%s)'
    return engine.execute(sql, data)


def select_latest(engine, account_no=None):
    """
    获取最新的持仓信息
    @param engine:
    @param account_no:
    """
    if account_no is None:
        sql = 'select * from account_holding where time_x=(select max(time_x) from account_holding)'
    else:
        sql = 'select * from account_holding where account_no="{0}" and time_x=(select max(time_x) from account_holding where account_no="{0}")'.format(
            account_no)
    rs_set = engine.execute(sql)
    rs = []
    for row in rs_set:
        rs.append(list(row))
    return rs


def delete(engine, account_no=None, time_x=None):
    if time_x is None:
        time_x = date.today().strftime('%Y-%m-%d')
    if account_no is None:
        sql = 'delete from account_holding where time_x="{}"'.format(time_x)
    else:
        sql = 'delete from account_holding where account_no="{}" and time_x="{}"'.format(account_no, time_x)
    return engine.execute(sql)


if __name__ == '__main__':
    from sqlalchemy import create_engine

    engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/quant_bee?charset=utf8')
    rs = select_latest(engine)
    print('')
