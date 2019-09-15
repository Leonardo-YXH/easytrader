# -*- coding:utf8 -*-

import matplotlib.pyplot as plt
from . import money_flow_statistic
from easytrader import log
import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime,timedelta

def test_monkey_seller():
    seller=None
    code='002848'
    tick=get_local_tick('tick_'+code+'_'+'2018-09-01_'+'2018-09-30.csv')
    low=tick.loc[0,'price']
    for index,item in tick.iterrows():
        if item['price']<low:
            low=item['price']
        elif item['price']/low>=1.01:
            buy_price=item['price']
            buy_date=index
            seller = money_flow_statistic.monkey_seller(code, buy_price=buy_price, volume=23, stop_loss=0.03,
                                                        moving_stop_loss=0.015)
        if seller is not None:
            if seller.check_sell(item):
                sell_price=item['price']
                sell_date=index
                show_tick(tick,buy_date,buy_price,sell_date,sell_price)
                break

def show_tick(tick,buy_date,buy_price,sell_date,sell_price):
    fig,ax=plt.subplots()
    tick['price'].plot(ax=ax)
    ax.scatter([buy_date,sell_date],[buy_price,sell_price],c='red')
    plt.show()


def download_tick(code,start,end):
    start_date=datetime.strptime(start,'%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    data=pd.DataFrame(columns=['time','price','change','volume','amount','type'])
    while start_date<=end_date:
        date=start_date.strftime('%Y-%m-%d')
        df=ts.get_tick_data(code,date,src='tt')
        if df is not None:
            print(date)
            df['date']=date
            data=data.append(df)
        start_date+=timedelta(days=1)

    data.index=np.arange(0,len(data))
    fn=log.get_root()+'/resource/'+'tick_'+code+'_'+start+'_'+end+'.csv'
    data.to_csv(fn,encoding='utf8',index_label='index')

def get_local_tick(fn):
    return pd.read_csv(log.get_root()+'/resource/'+fn,encoding='utf8')


if __name__=='__main__':
    # tick=ts.get_tick_data('000001','2018-09-28',src='tt')
    # tick.set_index(['time'],inplace=True)
    # show_tick(tick,500,10.12,1000,10.89)
    download_tick('002848','2018-09-01','2018-09-30')
    # df=get_local_tick('tick_'+'002848_'+'2018-09-01_'+'2018-09-30.csv')
    # print(df.empty)
    # test_monkey_seller()