# -*- coding:utf-8 -*-
"""

@author: leonardo
@created time: 2020-11-04
@last modified time:2020-11-04
"""
import os
from leo.database import trade_record_service_impl, mysql_proxy
from datetime import datetime, timedelta
import tushare as ts
import pandas as pd
from matplotlib import pyplot as plt
import mpl_finance as mpf
from matplotlib.pylab import date2num


def record_2_map(root_path, engine, backtesting_id):
    trade_record = trade_record_service_impl.select(engine, backtesting_id)
    trade_record_map = {}
    for row in trade_record:
        if row[1] not in trade_record_map:
            ticker_trade_time = []
            ticker_trade_time.append(row[2])
            trade_record_map[row[1]] = ticker_trade_time
        else:
            trade_record_map[row[1]].append(row[2])

    for ticker, ticker_trade_time in trade_record_map.items():
        for i in range(0, len(ticker_trade_time) - 1, 2):
            map_ticker(root_path, backtesting_id, ticker, ticker_trade_time[i], ticker_trade_time[i + 1])


def map_ticker(root_path, backtesting_id, ticker, long_date, short_date):
    start_date = long_date - timedelta(days=70)
    end_date = short_date + timedelta(days=70)
    ts.set_token('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    if ticker.startswith('60'):
        ts_code = ticker + '.SH'
    else:
        ts_code = ticker + '.SZ'
    day_bars = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date=start_date.strftime('%Y%m%d'),
                          end_date=end_date.strftime('%Y%m%d'))
    quotes = []
    long_short_prices = []
    long_short_dates = []
    for _, row in day_bars.iterrows():
        t = datetime.strptime(row['trade_date'], '%Y%m%d')
        x = date2num(t)
        if t.year == long_date.year and t.month == long_date.month and t.day == long_date.day:
            long_short_prices.append(row['open'])
            long_short_dates.append(x)
        elif t.year == short_date.year and t.month == short_date.month and t.day == short_date.day:
            long_short_prices.append(row['open'])
            long_short_dates.append(x)
        quotes.append((x, row['open'], row['high'], row['low'],
                       row['close']))

    fig, ax = plt.subplots(facecolor=(0, 0.3, 0.5), figsize=(12, 8))
    fig.subplots_adjust(bottom=0.1)
    ax.xaxis_date()
    plt.xticks(rotation=45)  # 日期显示的旋转角度
    plt.title(ticker)
    plt.xlabel('time')
    plt.ylabel('price')
    mpf.candlestick_ohlc(ax, quotes, width=0.7, colorup='r', colordown='green')  # 上涨为红色K线，下跌为绿色，K线宽度为0.7
    plt.scatter(x=long_short_dates, y=long_short_prices, color='blue')

    backtesting_id_strs = backtesting_id.split('_')
    strategy_id = backtesting_id_strs[0]
    fn = root_path + '/' + strategy_id + '/' + backtesting_id
    if not os.path.exists(fn):
        os.makedirs(fn)
    fn += ('/' + long_date.strftime('%Y%m%d') + '_' + ticker + '_' + short_date.strftime('%Y%m%d') + '.png')
    plt.savefig(fn)
    plt.close(fig)
    print('saved {}'.format(fn))


def record_analysis(root_path, engine, backtesting_id):
    sql='SELECT trade_record.*,70_screener_cn.market_cap from trade_record left JOIN 70_screener_cn on trade_record.ticker=70_screener_cn.ticker ' \
        'where trade_record.backtesting_id="{}" ORDER BY ticker,trade_time asc'.format(backtesting_id)
    trade_record=engine.execute(sql)
    trade_record_map = {}
    last_ticker=False
    df=[]
    for row in trade_record:
        if row[1] not in trade_record_map:
            ticker_trade_time = []
            ticker_trade_time.append(list(row))
            trade_record_map[row[1]] = ticker_trade_time
        else:
            trade_record_map[row[1]].append(list(row))

    for ticker, ticker_trade_time in trade_record_map.items():
        if len(ticker_trade_time)%2!=0:
            ticker_trade_time.pop(-1)
        df.extend(ticker_trade_time)

    df=pd.DataFrame(df,columns=['backtesting_id','ticker','trade_time','trade_type','price','market_cap'])
    fn=root_path+'/'+backtesting_id+'.csv'
    df.to_csv(fn)
    print('save {}'.format(fn))


if __name__ == '__main__':
    engine = mysql_proxy.get_connection('join_quant_backtesting')
    mysql_proxy.enable_np_encoder(engine)
    backtesting_id = '110_2020-11-21_15-23'
    # root_path = 'f:/joinquant/backtesting/trade_record'
    # record_2_map(root_path, engine, backtesting_id)

    root_path = 'f:/joinquant/backtesting/trade_analysis'
    record_analysis(root_path, engine, backtesting_id)
