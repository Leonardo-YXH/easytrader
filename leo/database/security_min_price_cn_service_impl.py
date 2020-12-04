# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-14
@last modified time:2020-09-14
"""
from sqlalchemy import create_engine

from leo.database import security_day_price_cn_service_impl

import tushare as ts
from datetime import datetime
import pandas as pd


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
        sql = 'SELECT ticker,time_x,open_x,high,low,close_x,volume,adj_close from security_min_price_cn where SECURITY_LOOKUP_ID in (SELECT ID from security_lookup_cn  where TICKER="{0}" and ins_type="stock") and time_x>="{1}" and time_x<="{2}" ORDER BY time_x asc'.format(
            ticker, start_date_str, end_date_str)

    else:
        sql = 'SELECT ticker,time_x,open_x,high,low,close_x,volume,adj_close from security_min_price_cn where SECURITY_LOOKUP_ID in (SELECT ID from security_lookup_cn  where TICKER="{0}" and ins_type="stock") and time_x>="{1}" ORDER BY time_x asc'.format(
            ticker, start_date_str)
    rs = []
    rs_set = engine.execute(sql)
    for row in rs_set:
        rs.append(list(row))
    return rs


def select_qfq(engine, ticker, start_date_str, end_date_str=None):
    """
    前复权的分钟数据
    :param engine:
    :param ticker:
    :param start_date_str:
    :param end_date_str:
    :return: [ticker,time_x,open_x,high,low,close_x,volume,adj_close] 将adj_close改成adj_factor
    """
    min_bars = select(engine, ticker, start_date_str, end_date_str)
    for min_bar in min_bars:
        min_bar.append(min_bar[1].strftime('%Y%m%d'))
    min_bars=pd.DataFrame(min_bars,columns=['ticker','time_x','open_x','high','low','close_x','volume','adj_close','trade_date'])
    # day_bars = security_day_price_cn_service_impl.select(engine, ticker, start_date_str[:10], end_date_str)

    if ticker.startswith('60'):
        ts_code = ticker + '.SH'
    else:
        ts_code = ticker + '.SZ'
    pro_api = ts.pro_api('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    adj_factor=pro_api.adj_factor(ts_code=ts_code,start_date=start_date_str.replace('-', ''),
                          end_date=end_date_str.replace('-', ''))[['trade_date', 'adj_factor']]

    data = min_bars.set_index('trade_date', drop=False).merge(adj_factor.set_index('trade_date'), left_index=True, right_index=True,
                                                        how='left')
    data['adj_factor'] = data['adj_factor'].fillna(method='bfill')
    return data
    day_bars_ts = ts.pro_bar(ts_code=ts_code, pro_api=pro_api, start_date=start_date_str.replace('-', ''),
                          end_date=end_date_str.replace('-', ''), adj='qfq')
    # day_bars = day_bars.reindex(index=day_bars.index[::-1])
    # day_bars = day_bars.values
    # if len(min_bars) / len(day_bars) != 240:
    #     raise Exception('day bar is not matching minute bar')
    # else:
    #     i = 0
    #     for min_bar in min_bars:
    #         if i % 240 == 0:  # 计算复权因子
    #             j = i // 240
    #             factor = min_bars[i + 239][5] / day_bars[j][5]
    #         min_bar[2] /= factor
    #         min_bar[3] /= factor
    #         min_bar[4] /= factor
    #         min_bar[5] /= factor
    #         i += 1
    #     return min_bars


def get_max_min_order_of_day(bars):
    """

    :param bars: [ [ticker,time_x,open_x,high,low,close_x,volume,adj_close], ]
    :return: 1:[low,high] ,-1:[high,low]
    """
    flag = 0
    high = -1
    low = 1000000
    for bar in bars:
        for i in [2, 3, 4, 5]:
            price = bar[i]
            if price > high:
                high = price
                flag = 1
            elif price < low:
                low = price
                flag = -1
    return flag


if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://readonly:gmbp12345@gz-cdb-qa6dqlyi.sql.tencentcdb.com:62589/gtechfin')
    rs = select_qfq(engine, '000090', '2020-09-01 09:30:00', '2020-09-15 15:00:00')
    print('exit')
