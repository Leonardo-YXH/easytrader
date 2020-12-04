# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-15
@last modified time:2020-09-15
"""
from leo.pattern import pattern_recognition
from leo.database import security_min_price_cn_service_impl, security_lookup_cn_wave_10_service_impl
from leo.tools import np_pymysql_encoder

import numpy as np
from sqlalchemy import create_engine
import tushare as ts
import pandas as pd


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
    min_prices = security_min_price_cn_service_impl.select_qfq(source_engine, ticker, start_date_str, end_date_str)
    if len(min_prices) == 0:
        print('{} has no min prices'.format(ticker))
        return
    prices = []
    current_factor = min_prices['adj_factor'].iloc[-1]
    pre_price, pre_factor = security_lookup_cn_wave_10_service_impl.select_latest(dest_engine, ticker, start_date_str)
    if pre_price is not None:
        prices.append(pre_price * pre_factor / current_factor)
    for _, row in min_prices.iterrows():  # 前复权
        factor = row['adj_factor'] / current_factor
        prices.append(row['open_x'] * factor)
        prices.append(row['high'] * factor)
        prices.append(row['low'] * factor)
        prices.append(row['close_x'] * factor)
    _, high_low_index, _ = pattern_recognition.get_local_high_low_point(prices, 0.1)
    data = []
    if pre_price is not None:
        high_low_index = np.array(high_low_index)[1:] - 1
    pre_row_index = -1
    for i in high_low_index:
        row = []
        row_index = i // 4
        col_index = i % 4 + 2  # open_x前面有ticker,time_x
        row.append(ticker)
        row.append(min_prices.iloc[row_index, 1].strftime('%Y-%m-%d %X'))
        row.append(min_prices.iloc[row_index, col_index])
        row.append(min_prices.iloc[row_index, -1])
        data.append(row)
    if len(data) > 0:
        security_lookup_cn_wave_10_service_impl.insert_on_duplicate_update(dest_engine, data)


def cal_high_low_point_of_sse(pro_api, source_engine, dest_engine, start_date_str, end_date_str):
    """

    :param source_engine:
    :param dest_engine:
    :param start_date_str:
    :param end_date_str:
    :return:
    """

    stock_df = pro_api.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
    stock_df = stock_df[3245:]  # last
    stock_size = len(stock_df)
    i = 0
    for idx, row in stock_df.iterrows():
        i += 1
        ticker = row['ts_code'][:6]
        cal_high_low_point_of_stock(source_engine, dest_engine, ticker, start_date_str, end_date_str)
        print('{} finished at {}/{}'.format(ticker, i, stock_size))


def get_msci_cn():
    df = pd.read_csv('f://MSCITable.csv', encoding='gbk', sep='\t+')
    stocks = []
    for _, row in df.iterrows():
        ticker = row['代码']
        if ticker.startswith('SZ'):
            ticker = ticker[2:] + '.XSHE'
        else:
            ticker = ticker[2:] + '.XSHG'
        stocks.append(ticker)
    return stocks


if __name__ == '__main__':
    # pro_api = ts.pro_api('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    # source_engine = create_engine(
    #     'mysql+pymysql://readonly:gmbp12345@gz-cdb-qa6dqlyi.sql.tencentcdb.com:62589/gtechfin')
    # dest_engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/quant_bee?charset=utf8')
    # np_pymysql_encoder.enable_np_encoder(dest_engine)
    # start_date_str = '2020-02-04 09:31:00'
    # end_date_str = '2020-09-17 15:00:00'
    # cal_high_low_point_of_stock(source_engine, dest_engine, '000715', start_date_str, end_date_str)
    # cal_high_low_point_of_sse(pro_api,source_engine, dest_engine, start_date_str, end_date_str)
    get_msci_cn()
