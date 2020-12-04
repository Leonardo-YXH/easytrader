# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-18
@last modified time:2020-09-18
"""

import numpy as np
from sqlalchemy import create_engine,event
import tushare as ts

def add_own_encoders(conn, cursor, query, *args):
    cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
    cursor.connection.encoders[np.int32] = lambda value, encoders: int(value)



def enable_np_encoder(engine):
    """
    py_mysql支持np.float64 translate
    :param engine:
    :return:
    """
    event.listen(engine, "before_cursor_execute", add_own_encoders)

def select_latest(engine,ticker,time_x):
    """
    获取离time_x最近的一个
    :param engine:
    :param ticker:
    :param time_x:
    :return:
    """
    sql='select price,adj_factor from security_lookup_cn_wave_10 where ticker="{}" and time_x<="{}" ORDER BY time_x desc limit 1'.format(ticker,time_x)
    rs_set=engine.execute(sql)
    price=None
    adj_factor=None
    for p,f in rs_set:
        price=p
        adj_factor=f

    return price,adj_factor

def get_local_high_low_point(prices, pnl_threshold):
    """
    计算局部最高最低点
    :param prices:
    :param pnl_threshold: 趋势阈值
    :return:
    """
    if len(prices) == 0:
        return None, None, None

    pnl_threshold_up = 1 + pnl_threshold
    pnl_threshold_down = 1 - pnl_threshold
    high = prices[0]
    low = prices[0]
    high_i = 0
    low_i = 0
    flag = 0  # 1:当前最高点，0：初始化，-1：当前最低点
    rs = []
    rs_index = []
    for i in range(len(prices)):
        v = prices[i]
        if flag == 0:
            if v > high:
                high = v
                high_i = i
                if high / low > pnl_threshold_up:
                    rs_index.append(low_i)
                    rs_index.append(high_i)
                    rs.append(low)
                    rs.append(high)
                    flag = 1
                    low = high
            elif v < low:
                low = v
                low_i = i
                if low / high < pnl_threshold_down:
                    rs_index.append(high_i)
                    rs_index.append(low_i)
                    rs.append(high)
                    rs.append(low)
                    flag = -1
                    high = low
        elif flag == 1:
            if v > high:  # update current high
                high = v
                low = v
                rs_index[-1] = i
                rs[-1] = v
            elif v < low:
                low = v
                if low / high < pnl_threshold_down:
                    rs_index.append(i)
                    rs.append(low)
                    flag = -1
                    high = low
        elif flag == -1:
            if v < low:
                low = v
                high = v
                rs_index[-1] = i
                rs[-1] = v
            elif v > high:
                high = v
                if high / low > pnl_threshold_up:
                    rs_index.append(i)
                    rs.append(high)
                    flag = 1
                    low = high

    return rs, rs_index, flag

def insert_on_duplicate_update(engine,data):
    """

    :param engine:
    :param data:
    :return:
    """
    sql='insert into security_lookup_cn_wave_10(ticker,time_x,price,adj_factor)' \
        ' values (%s,%s,%s,%s)' \
        ' on duplicate key update ticker=values(ticker),time_x=values(time_x),price=values(price),adj_factor=values(adj_factor)'
    return engine.execute(sql,data)

def cal_high_low_point_of_stock(source_engine, dest_engine, ticker, start_date_str, end_date_str):
    """

    :param source_engine: 分钟数据源
    :param dest_engine:
    :param ticker:
    :param start_date_str: yyyy-mm-dd hh:mm:ss
    :param end_date_str:
    :return:
    """
    # column=[ticker,time_x,open_x,high,low,close_x,volume,adj_close,trade_date,adj_factor]
    min_prices=None
    if len(min_prices)==0:
        print('{} has no min prices'.format(ticker))
        return
    prices = []
    current_factor = min_prices['adj_factor'].iloc[-1]
    pre_price, pre_factor = select_latest(dest_engine, ticker, start_date_str)
    if pre_price is not None:
        prices.append(pre_price * pre_factor / current_factor)
    for _, row in min_prices.iterrows():  # 前复权
        factor = row['adj_factor'] / current_factor
        prices.append(row['open_x'] * factor)
        prices.append(row['high'] * factor)
        prices.append(row['low'] * factor)
        prices.append(row['close_x'] * factor)
    _, high_low_index, _ = get_local_high_low_point(prices, 0.1)
    data = []
    if pre_price is not None:
        high_low_index = np.array(high_low_index)[1:] - 1

    for i in high_low_index:
        row = []
        row_index = i // 4
        col_index = i % 4 + 2  # open_x前面有ticker,time_x
        row.append(ticker)
        row.append(min_prices.iloc[row_index, 1].strftime('%Y-%m-%d %X'))
        row.append(min_prices.iloc[row_index, col_index])
        row.append(min_prices.iloc[row_index, -1])
        data.append(row)
    if len(data)>0:
        insert_on_duplicate_update(dest_engine, data)

def cal_high_low_point_of_sse(source_engine, dest_engine, start_date_str, end_date_str):
    """

    :param dest_engine:
    :param start_date_str:
    :param end_date_str:
    :return:
    """

    stock_df = None
    stock_df=stock_df[3245:] # last
    stock_size = len(stock_df)
    i = 0
    for idx, row in stock_df.iterrows():
        i += 1
        ticker = row['ts_code'][:6]
        cal_high_low_point_of_stock(source_engine, dest_engine, ticker, start_date_str, end_date_str)
        print('{} finished at {}/{}'.format(ticker, i, stock_size))


if __name__ == '__main__':
    pro_api = ts.pro_api('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    source_engine = create_engine(
        'mysql+pymysql://readonly:gmbp12345@gz-cdb-qa6dqlyi.sql.tencentcdb.com:62589/gtechfin')
    dest_engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/quant_bee?charset=utf8')
    enable_np_encoder(dest_engine)
    start_date_str = '2020-01-01 09:30:00'
    end_date_str = '2020-09-17 15:00:00'
    cal_high_low_point_of_stock(source_engine, dest_engine, '000090', start_date_str, end_date_str)
    # cal_high_low_point_of_sse(pro_api,source_engine, dest_engine, start_date_str, end_date_str)