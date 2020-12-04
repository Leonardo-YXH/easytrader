# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-14
@last modified time:2020-09-14
"""
from sqlalchemy import create_engine


def select(engine, ticker, start_date_str, end_date_str=None):
    """
    未复权的分钟数据
    :param engine:
    :param ticker:
    :param start_date_str:
    :param end_date_str:
    :return:
    """
    if end_date_str is not None:
        sql = 'SELECT ticker,time_x,open_x,high,low,close_x,volume,adj_close from security_day_price_cn where SECURITY_LOOKUP_ID in (SELECT ID from security_lookup_cn  where TICKER="{0}" and ins_type="stock") and time_x>="{1}" and time_x<="{2}" ORDER BY time_x asc'.format(
            ticker, start_date_str, end_date_str)

    else:
        sql = 'SELECT ticker,time_x,open_x,high,low,close_x,volume,adj_close from security_day_price_cn where SECURITY_LOOKUP_ID in (SELECT ID from security_lookup_cn  where TICKER="{0}" and ins_type="stock") and time_x>="{1}" ORDER BY time_x asc'.format(
            ticker, start_date_str)
    rs = []
    rs_set = engine.execute(sql)
    for row in rs_set:
        rs.append(list(row))
    return rs



if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://readonly:gmbp12345@gz-cdb-qa6dqlyi.sql.tencentcdb.com:62589/gtechfin')
    rs = select(engine, '000090', '2020-09-01')
    print('exit')
