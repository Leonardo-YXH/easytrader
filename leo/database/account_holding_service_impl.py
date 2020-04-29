# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-04-29
@last modified time:2020-04-29
"""
import sqlalchemy


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


def select_latest(engine, account_no=None):
    """
    获取最新的持仓信息
    @param engine:
    @param account_no:
    """
    sql = 'select * from account_holding where account_no="{0}" and date_format(time_x,"%Y%m%d")=(select date_format(max(time_x,"%Y%m%d")) from account_holding where account_no="{0}")'.format(
        account_no)
    return list(engine.execute(sql))
