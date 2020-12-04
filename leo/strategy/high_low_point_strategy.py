# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-09-19
@last modified time:2020-09-19
"""
import tushare as ts
import pandas as pd
from sqlalchemy import create_engine

from leo.pattern import pattern_recognition
from leo.database import security_lookup_cn_wave_10_service_impl


def wave_raise_up(start_date_str):
    pro_api = ts.pro_api('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    dest_engine = create_engine('mysql+pymysql://readonly:045715@106.14.153.239:3306/quant_bee?charset=utf8')
    stock_df = pro_api.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')

    # stock_df=stock_df[stock_df['ts_code'].isin(['000797.SZ','300712.SZ'])]
    stock_size = len(stock_df)
    j = 0
    for idx, row in stock_df.iterrows():
        j += 1
        ticker = row['ts_code'][:6]
        waves = security_lookup_cn_wave_10_service_impl.select_from_to_now(dest_engine, ticker, start_date_str)
        if len(waves) == 0:
            continue

        waves = pd.DataFrame(waves, columns=['time_x', 'trade_date', 'price'])
        adj_factor = pro_api.adj_factor(ts_code=row['ts_code'], start_date=start_date_str.replace('-', ''), )[
            ['trade_date', 'adj_factor']]

        data = waves.set_index('trade_date', drop=False).merge(adj_factor.set_index('trade_date'), left_index=True,
                                                               right_index=True,
                                                               how='left')
        data.sort_values('time_x', inplace=True, ascending=False)
        data['adj_factor'] = data['adj_factor'].fillna(method='bfill')
        data['adj_price'] = data['price'] * data['adj_factor'] / data['adj_factor'].iloc[0]

        limit_size = 4
        # if len(data) >= limit_size:
        is_up = pattern_recognition.is_wave_raise_up(data['adj_price'][:limit_size].values)
        if is_up:
            print('{} '.format(ticker))

        # if len(data)>2:
        #     adj_price=data['adj_price']
        #     for i in range(1,len(adj_price)-1):
        #         side=(adj_price.iloc[i]-adj_price.iloc[i-1])*(adj_price.iloc[i+1]-adj_price.iloc[i])
        #         if side>0:
        #             if ticker.startswith('6'):
        #                 ticker_ts=ticker+'.XSHG'
        #             else:
        #                 ticker_ts = ticker + '.XSHE'
        #             print('["{}", "{}"],'.format(ticker_ts,data['time_x'].iloc[i-1]))
        #             break

        # print('{} finished at {}/{}'.format(ticker, j, stock_size))


if __name__ == '__main__':
    start_date_str = '2020-08-01'
    wave_raise_up(start_date_str)
