# -*- coding:utf8 -*-
import tushare as ts
from datetime import timedelta,date
import math

def get_previous_trader_date(date):
    """
    获取上一个交易日
    :param date: datetime
    :return: datetime,datetime_str
    """
    start = date - timedelta(days=1)
    start_str = start.strftime('%Y-%m-%d')
    while ts.is_holiday(start_str):
        start = start - timedelta(days=1)
        start_str = start.strftime('%Y-%m-%d')
    return start,start_str

def get_previous_trader_date_by_code(date,code):
    """
    获取date的上一个非停牌交易日
    :param date: datetime
    :param code:
    :return: datetime
    """
    pro=ts.pro_api('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    #下面是官方的api_token
    #fa381e2536d016fd126110367ac47cf9da5fa515a784a19cf38f5c41
    date,start_str=get_previous_trader_date(date)
    date_str=date.strftime('%Y%m%d')

    while pro.daily(ts_code=code,start_date=date_str,end_date=date_str).loc[0,'vol'] ==0:
        date, start_str = get_previous_trader_date(date)
        date_str = date.strftime('%Y%m%d')
    return date


def calculate_limit_up(price):
    """
    10%的增长，小数点第三位四舍五入（排除st 5%的设定）
    :param price:
    :return:
    """
    price*=1.1
    price*=100
    price+=0.5
    price=math.floor(price)
    return price/100.0

def calculate_limit_down(price):
    """
    10%的跌幅，小数点第三位四舍五入（排除st 5%的设定）
    :param price:
    :return:
    """
    price*=0.9
    price*=100
    price+=0.5
    price=math.floor(price)
    return price/100.0

def calculate_limit_up_n(code,days=14,end_date=None):
    """计算连板天数"""
    if end_date is None:
        end_date=date.today()
    start_date=end_date-timedelta(days=days)
    df=ts.bar(code,ts.get_apis(),start_date=start_date.strftime('%Y-%m-%d'),end_date=end_date.strftime('%Y-%m-%d'),freq='D',adj='qfq')
    upn=0
    for _,item in df.iterrows():
        if item['vol']==0:#跳过停牌
            continue
        if item['p_change']>9.8:
            upn+=1
        else:
            break
    return upn



if __name__=='__main__':
    date=date.today()
    print(get_previous_trader_date_by_code(date,code='603032.SH'))