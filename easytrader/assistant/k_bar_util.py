# -*- coding:utf8 -*-
import pandas as pd

class K_Bar(object):
    def __init__(self,time_step=5):
        """

        :param time_step: 单位:minute,且必须是60的约数
        """
        self._time_step=time_step
        self._tick_data=pd.DataFrame(columns=['open','close','high','low','volume','amount'])
        self._tick_index='00:00:00'

    def add_tick(self,tick):
        minute_tick=int(tick['time'][3:5])
        minute_tick-=(minute_tick%self._time_step)
        tick_index=tick['time'][0:3]+str(minute_tick)+':00'
        price=float(tick['price'])
        if tick_index==self._tick_index:#the same area
            self._tick_data.loc[tick_index, 'close'] = price
            if self._tick_data.loc[tick_index,'high']<price:
                self._tick_data.loc[tick_index, 'high'] = price
            if self._tick_data.loc[tick_index, 'low'] > price:
                self._tick_data.loc[tick_index, 'low'] = price
            self._tick_data.loc[tick_index, 'volume'] += float(tick['volume']) / 100
            self._tick_data.loc[tick_index, 'amount'] += float(tick['amount'])
        else:#next slice,init
            self._tick_data.loc[tick_index, 'high'] = price
            self._tick_data.loc[tick_index, 'low'] = price
            self._tick_data.loc[tick_index, 'open'] = price
            self._tick_data.loc[tick_index, 'close'] = price
            self._tick_data.loc[tick_index, 'volume'] = float(tick['volume'])/100
            self._tick_data.loc[tick_index, 'amount'] = float(tick['amount'])
            self._tick_index=tick_index

    def get_previous_bar(self,previous_count=0):
        return self._tick_data.loc[self._tick_data.index[-1-previous_count]]

    def get_bar(self,index_label):
        return self._tick_data.loc[index_label]

def test1():
    import tushare as ts
    tick_data=ts.get_tick_data('000001','2018-08-30',src='tt')
    k_bar=K_Bar(time_step=2)
    for _,tick in tick_data.iterrows():
        k_bar.add_tick(tick)
    print(k_bar)
if __name__=='__main__':
    test1()