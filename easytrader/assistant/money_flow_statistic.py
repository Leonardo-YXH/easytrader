# -*- coding:utf-8 -*-
import math
import tushare as ts
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import date, timedelta
import matplotlib.pyplot as plt
from easytrader.assistant import k_bar_util,market_trader_util



class eagle_eye_bot(object):
    def __init__(self, stock_list=[]):
        self._scheduler = BlockingScheduler()
        self.stock_list = stock_list
        self._money_flows = {}
        self._start_time = {}
        for stock in stock_list:
            self._money_flows[stock] = money_flow_level()
            self._start_time[stock] = '00:00:00'

    def start(self):
        self._scheduler.add_job(self._start_monitor_job, 'cron', day_of_week='mon-fri', hour=9, minute=29,
                                second=58)  # 启动监控9:29:58,先获取集合竞价的数据
        self._scheduler.add_job(self._end_monitor_job, 'cron', day_of_week='mon-fri', hour=11, minute=30,
                                second=5)  # 结束上午的监控11:30:05
        self._scheduler.add_job(self._start_monitor_job, 'cron', day_of_week='mon-fri', hour=13, minute=0,
                                second=0)  # 启动下午的监控
        self._scheduler.add_job(self._end_monitor_job, 'cron', day_of_week='mon-fri', hour=15, minute=0,
                                second=5)  # 结束下午的监控15:00:05
        try:
            self._scheduler.start()
            print('start to monitor tick data...')
        except(KeyboardInterrupt, SystemExit):
            self._scheduler.remove_all_jobs()

    def _start_monitor_job(self):
        self._scheduler.add_job(self.__stock_monitor_on_second, 'interval', seconds=3, id='monitor_tick')

    def _end_monitor_job(self):
        self._scheduler.remove_job(job_id='monitor_tick')

    def add_stock(self, stock_code, levels=[]):
        """
        add code to be monitored
        :param stock_code:
        :return:
        """
        levels = fit_levels(levels)
        self.stock_list.append(stock_code)
        self._money_flows[stock_code] = money_flow_level(levels[0], levels[1], levels[2], levels[3])
        self._start_time[stock_code] = '00:00:00'

    def remove_stock(self, stock_code):
        """

        :param stock_code:
        :return:
        """
        self.stock_list.remove(stock_code)
        del self._money_flows[stock_code]
        del self._start_time[stock_code]

    def get_stock_money_flow(self, stock_code):
        """

        :param stock_code:
        :return:
        """
        return self._money_flows[stock_code]

    def __stock_monitor_on_second(self):  # 定时获取tick数据处理
        data = ts.get_realtime_quotes(self.stock_list)
        for _, item in data.iterrows():
            if item['time'] != self._start_time[item['code']]:  # 是否是新成交的数据
                self.__add_tick(item)
                self._start_time[item['code']] = item['time']

    def __add_tick(self, tick_data):
        price = float(tick_data['price'])
        if price <= float(tick_data['ask']):  # 小于等于买一价，卖盘
            tick_type = -1
        elif price >= float(tick_data['bid']):  # 大于等于卖一价，买盘
            tick_type = 1
        else:
            tick_type = 0
        self._money_flows[tick_data['code']].add_tick(float(tick_data['amount']), float(tick_data['volume']), tick_type)


class money_flow_level(object):
    def __init__(self, level1=20000, level2=100000, level3=300000, level4=1000000):
        """
        五档金额区间
        :param level1: 小单上限金额
        :param level2: 中单上限金额
        :param level3: 大单上限金额
        :param level4: 超大单上限金额
        """
        self.level1 = level1
        self.level2 = level2
        self.level3 = level3
        self.level4 = level4
        self.level1_amount_buy = 0
        self.level2_amount_buy = 0
        self.level3_amount_buy = 0
        self.level4_amount_buy = 0
        self.level5_amount_buy = 0  # 主力流入金额
        self.level1_volume_buy = 0
        self.level2_volume_buy = 0
        self.level3_volume_buy = 0
        self.level4_volume_buy = 0
        self.level5_volume_buy = 0

        self.level1_amount_sell = 0
        self.level2_amount_sell = 0
        self.level3_amount_sell = 0
        self.level4_amount_sell = 0
        self.level5_amount_sell = 0
        self.level1_volume_sell = 0
        self.level2_volume_sell = 0
        self.level3_volume_sell = 0
        self.level4_volume_sell = 0
        self.level5_volume_sell = 0

        self.amount = 0
        self.volume = 0

    def add_tick(self, amount, volume, type):
        """

        :param amount: 成交额
        :param volume: 成交量,单位:手
        :param type: 卖盘<0，买盘>0，中性盘=0
        :return:
        """
        if amount < self.level1:
            if type > 0:  # 买盘
                self.level1_amount_buy += amount
                self.level1_volume_buy += volume
            elif type < 0:  # 卖盘
                self.level1_amount_sell += amount
                self.level1_volume_sell += volume
        elif amount < self.level2:
            if type > 0:  # 买盘
                self.level2_amount_buy += amount
                self.level2_volume_buy += volume
            elif type < 0:  # 卖盘
                self.level2_amount_sell += amount
                self.level2_volume_sell += volume
        elif amount < self.level3:
            if type > 0:  # 买盘
                self.level3_amount_buy += amount
                self.level3_volume_buy += volume
            elif type < 0:  # 卖盘
                self.level3_amount_sell += amount
                self.level3_volume_sell += volume
        elif amount < self.level4:
            if type > 0:  # 买盘
                self.level4_amount_buy += amount
                self.level4_volume_buy += volume
            elif type < 0:  # 卖盘
                self.level4_amount_sell += amount
                self.level4_volume_sell += volume
        else:
            if type > 0:  # 买盘
                self.level5_amount_buy += amount
                self.level5_volume_buy += volume
            elif type < 0:  # 卖盘
                self.level5_amount_sell += amount
                self.level5_volume_sell += volume
        self.amount += amount
        self.volume += volume

    def add_tick_2(self, amount, volume, type):
        """

        :param amount: 成交额
        :param volume: 成交量,单位:手
        :param type: 卖盘，买盘，中性盘
        :return:
        """
        if amount < self.level1:
            if type == u'买盘':  # 买盘
                self.level1_amount_buy += amount
                self.level1_volume_buy += volume
            elif type == u'卖盘':  # 卖盘
                self.level1_amount_sell += amount
                self.level1_volume_sell += volume
        elif amount < self.level2:
            if type == u'买盘':  # 买盘
                self.level2_amount_buy += amount
                self.level2_volume_buy += volume
            elif type == u'卖盘':  # 卖盘
                self.level2_amount_sell += amount
                self.level2_volume_sell += volume
        elif amount < self.level3:
            if type == u'买盘':  # 买盘
                self.level3_amount_buy += amount
                self.level3_volume_buy += volume
            elif type == u'卖盘':  # 卖盘
                self.level3_amount_sell += amount
                self.level3_volume_sell += volume
        elif amount < self.level4:
            if type == u'买盘':  # 买盘
                self.level4_amount_buy += amount
                self.level4_volume_buy += volume
            elif type == u'卖盘':  # 卖盘
                self.level4_amount_sell += amount
                self.level4_volume_sell += volume
        else:
            if type == u'买盘':  # 买盘
                self.level5_amount_buy += amount
                self.level5_volume_buy += volume
            elif type == u'卖盘':  # 卖盘
                self.level5_amount_sell += amount
                self.level5_volume_sell += volume
        self.amount += amount
        self.volume += volume

class monkey_seller(object):
    """
    排除几类stock不作考虑：[ST,从当前日期往前停牌超过10天]
    """
    def __init__(self,code,buy_price,volume,stop_loss=0.03,moving_stop_loss=0.015):
        self._code=code
        self._buy_price=buy_price
        self._volume=volume
        self._stop_loss=1-stop_loss
        self._moving_stop_loss=moving_stop_loss

        self._high=0
        self._current_price=buy_price
        self._k_bar=k_bar_util.K_Bar(time_step=2)
        self._is_limit_up=False #是否涨停
        self._limit_up_price=0
        self._pre_bar=None

        if code.startswith('60'):#以60开头的为沪市
            self._code_symbol=self._code+'.SH'
        else:#以000开头的为深市
            self._code_symbol = self._code + '.SZ'

    def init_previous_data(self):
        """初始化上一个交易日数据（且不是停牌数据），必须在每日开盘时执行一遍,如果超过10天都没数据则置空（除非ST或者特殊情况比如中兴贸易战，否则停牌一般不会超过10天）"""
        pro=ts.pro_api()
        previous_trade_day=date.today()-timedelta(days=10)
        previous_trade_day=previous_trade_day.strftime('%Y%m%d')
        data=pro.daily(ts_code=self._code_symbol,start_date=previous_trade_day,end_date=date.today().strftime('%Y%m%d'))
        for _,item in data.iterrows():
            if item['vol']!=0:
                self._pre_bar=item
                break
            else:
                continue

        self._limit_up_price=market_trader_util.calculate_limit_up(float(ts.get_realtime_quotes(self._code).loc[0,'pre_close']))

    def update_today_data_as_pre_data(self):
        """每天收盘后更新数据作为明天的历史K数据"""
        pass

    def check_sell(self,tick_data):
        """
        是否符合卖出条件
        :param tick_data:
        :return:
        """
        self._current_price=float(tick_data['price'])
        if self._high < self._current_price:
            self._high = self._current_price
        self._k_bar.add_tick(tick_data)

        if self._strategy_stop_loss():
            return True
        if self._strategy_cross_down_yestoday_low():
            return True

        return False

    def _strategy_stop_loss(self):
        """
        低于止损价直接卖出
        :return:
        """
        if self._current_price/self._buy_price<self._stop_loss:
            return True
    def _strategy_cross_down_yestoday_low(self):
        """突破昨日最低价直接卖出"""
        if self._current_price<self._yestoday_low:
            return True

    def _strategy_3(self,tick_data):

        pre_close=float(tick_data['pre_close'])
        income_point= self._high/pre_close-1
        if income_point>0.03:
            if self._current_price<(pre_close+self._high)/2:
                return True

        return False

    def _strategy_limit_up(self):
        if self._is_limit_up:
            pass

    def _strategy_7_to_10(self):
        """"""



def fit_levels(levels=[20000, 100000, 300000, 1000000]):
    """
    如果levels的size小于4，补齐levels
    :param levels:
    :return:
    """
    level_size = len(levels)
    if level_size > 4:
        raise Exception('level size must be less than 5')
    while level_size < 4:
        level_size += 1
        levels.append(100000000 + level_size)  # 上限1亿，一般很少有一次成交额超1亿
    return levels


def get_history_money_flow(stock_code=None, start_date=None, end_date=None, levels=[20000, 100000, 300000, 1000000]):
    """
    统计从start_date到end_date各区间的成交量和成交额
    :param stock_code:
    :param start_date: date类型
    :param end_date: date类型,不包括end_date
    :param levels:
    :return:
    """
    levels = fit_levels(levels)
    money_flow = money_flow_level(levels[0], levels[1], levels[2], levels[3])
    while start_date < end_date:
        start = start_date.strftime('%Y-%m-%d')
        start_date += timedelta(days=1)
        tick_data = ts.get_tick_data(stock_code, date=start, src='tt')
        if tick_data is None or tick_data.empty:
            continue
        for _, item in tick_data.iterrows():
            money_flow.add_tick_2(item['amount'], item['volume'], item['type'])

    return money_flow


def get_history_money_flow_1(stock_code=None, start_date=None, end_date=None,trade_days=5, amount_threshold=100000):
    """
    统计从start_date到end_date各区间的成交量和成交额
    :param stock_code:
    :param start_date: date类型
    :param end_date: date类型
    :param trade_days:多少个交易日
    :param amount_threshold:大单阈值，默认10w元
    :return:amount_buy,volume_buy,amount_sell,volume_sell
    """
    amount_buy = 0
    amount_sell = 0
    volume_buy = 0
    volume_sell = 0
    trade_days_count=0
    while start_date < end_date and trade_days_count<trade_days:
        start = end_date.strftime('%Y-%m-%d')
        end_date -= timedelta(days=1)
        tick_data = ts.get_tick_data(stock_code, date=start, src='tt')
        if tick_data is None or tick_data.empty:
            continue
        trade_days_count+=1

        huge_data = tick_data[tick_data['amount'] > amount_threshold]
        buy_data = huge_data[huge_data['type'] == u'买盘']
        sell_data = huge_data[huge_data['type'] == u'卖盘']
        amount_buy += buy_data['amount'].sum()
        amount_sell += sell_data['amount'].sum()
        volume_buy += buy_data['volume'].sum()
        volume_sell += sell_data['volume'].sum()

    return [amount_buy,volume_buy,amount_sell,volume_sell]

def calculate_price_rate(stock_code=None, start_date=None, end_date=None,trade_days=5, amount_threshold=100000,price=1):
    """
    从end_date倒数trade_days个交易日的数据累积
    :param stock_code:
    :param start_date:
    :param end_date:
    :param trade_days:
    :param amount_threshold:
    :param price: 当前价格
    :return: 返回值越大可买性越高。>1W低位吸筹，>1K高位吸筹，伴随着剧烈拉升，<1K&>900高位出货，<100出货尽头伴随阴跌
    """
    rs=get_history_money_flow_1(stock_code=stock_code,start_date=start_date,end_date=end_date,trade_days=trade_days,amount_threshold=amount_threshold)
    expect_price=(rs[0]-rs[2])/(rs[1]-rs[3])
    expect_price/=100.0
    rate=expect_price/price
    if rs[1]>rs[3]:
        if rs[0]>rs[2]:
            return expect_price,1000+rate
        else:
            return expect_price,10000-rate
    else:
        if rs[0]>rs[2]:
            return expect_price,-rate
        else:
            return expect_price,900+rate

def get_today_money_flow(stock_code=None, levels=[20000, 100000, 300000, 1000000]):
    """
    统计从start_date到end_date各区间的成交量和成交额
    :param stock_code:
    :param start_date: date类型
    :param end_date: date类型,不包括end_date
    :param levels:
    :return:
    """
    levels = fit_levels(levels)
    money_flow = money_flow_level(levels[0], levels[1], levels[2], levels[3])
    start = date.today().strftime('%Y-%m-%d')
    tick_data = ts.get_today_ticks(stock_code)
    if tick_data is None or tick_data.empty:
        return money_flow_level()
    for _, item in tick_data.iterrows():
        money_flow.add_tick_2(item['amount'], item['volume'], item['type'])
    return money_flow


def draw_money_flow_by_pie(money_flow):
    # sell:green,buy:red
    colors = ['#00ff00', '#00ee00', '#00cd00', '#008b00', '#006400', '#640000', '#8b0000', '#cd0000', '#ee0000',
              '#ff0000']
    fracs = [money_flow.level1_amount_sell, money_flow.level2_amount_sell, money_flow.level3_amount_sell,
             money_flow.level4_amount_sell, money_flow.level5_amount_sell,
             money_flow.level5_amount_buy, money_flow.level4_amount_buy, money_flow.level3_amount_buy,
             money_flow.level2_amount_buy, money_flow.level1_amount_buy]
    labels = ['level1_sell', 'level2_sell', 'level3_sell', 'level4_sell', 'level5_sell',
              'level5_buy', 'level4_buy', 'level3_buy', 'level2_buy', 'level1_buy']
    plt.pie(x=fracs, labels=labels, colors=colors)
    plt.show()


def draw_money_flow_by_bar(money_flow):
    x1 = [0, 1, 2, 3, 4,5]
    x2 = [0.4, 1.4, 2.4, 3.4, 4.4,5.4]
    amount_sell=sum([money_flow.level1_amount_sell, money_flow.level2_amount_sell, money_flow.level3_amount_sell,
          money_flow.level4_amount_sell, money_flow.level5_amount_sell])
    amount_buy=sum([money_flow.level1_amount_buy, money_flow.level2_amount_buy, money_flow.level3_amount_buy,
          money_flow.level4_amount_buy, money_flow.level5_amount_buy])
    y1 = [money_flow.level1_amount_sell, money_flow.level2_amount_sell, money_flow.level3_amount_sell,
          money_flow.level4_amount_sell, money_flow.level5_amount_sell,amount_sell]
    y2 = [money_flow.level1_amount_buy, money_flow.level2_amount_buy, money_flow.level3_amount_buy,
          money_flow.level4_amount_buy, money_flow.level5_amount_buy,amount_buy]
    volume_sell=sum([money_flow.level1_volume_sell, money_flow.level2_volume_sell, money_flow.level3_volume_sell,
          money_flow.level4_volume_sell, money_flow.level5_volume_sell])
    volume_buy=sum([money_flow.level1_volume_buy, money_flow.level2_volume_buy, money_flow.level3_volume_buy,
          money_flow.level4_volume_buy, money_flow.level5_volume_buy])
    z1 = [money_flow.level1_volume_sell, money_flow.level2_volume_sell, money_flow.level3_volume_sell,
          money_flow.level4_volume_sell, money_flow.level5_volume_sell,volume_sell]
    z2 = [money_flow.level1_volume_buy, money_flow.level2_volume_buy, money_flow.level3_volume_buy,
          money_flow.level4_volume_buy, money_flow.level5_volume_buy,volume_buy]
    m1 = [money_flow.level1_amount_sell / money_flow.level1_volume_sell,
          money_flow.level2_amount_sell / money_flow.level2_volume_sell,
          money_flow.level3_amount_sell / money_flow.level3_volume_sell,
          money_flow.level4_amount_sell / (money_flow.level4_volume_sell + 0.001),
          money_flow.level5_amount_sell / (money_flow.level5_volume_sell + 0.001),
          amount_sell/volume_sell]
    m2 = [money_flow.level1_amount_buy / money_flow.level1_volume_buy,
          money_flow.level2_amount_buy / money_flow.level2_volume_buy,
          money_flow.level3_amount_buy / money_flow.level3_volume_buy,
          money_flow.level4_amount_buy / (money_flow.level4_volume_buy + 0.001),
          money_flow.level5_amount_buy / (money_flow.level5_volume_buy + 0.001),
          amount_buy/volume_buy]

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax1.bar(x1, y1, 0.4, color='green')
    ax1.bar(x2, y2, 0.4, color='red', label=u'成交额')

    ax2 = ax1.twinx()
    plt.plot(x1, m1, 'yo')
    plt.plot(x2, m2, 'yo')

    ax3=fig.add_subplot(212)
    ax3.bar(x1, z1, 0.4, color='green')
    ax3.bar(x2, z2, 0.4, color='red', label=u'成交量')

    plt.show()

def test_calculate_price_rate(stock_code='000001',trade_days=5,end_date=None):
    # end_date=date.today()
    start_date=end_date-timedelta(days=15)
    realtime_tick=ts.get_realtime_quotes(stock_code)
    price=float(realtime_tick['price'].iat[0])
    expect_price,rate=calculate_price_rate(stock_code,start_date,end_date,trade_days,amount_threshold=100000,price=price)
    print(expect_price,rate)

def test_trader_log():
    import logging
    log=logging.getLogger('trader')
    log.info('buy 100 vol at price 4.5')

if __name__ == '__main__':
    start_date = date.today() - timedelta(days=0)
    # money_flow = get_history_money_flow('002925', start_date=start_date, end_date=date.today()+timedelta(days=1))
    # money_flow = get_today_money_flow('603706')
    # draw_money_flow_by_bar(money_flow)
    #print(money_flow.volume)
    # end_date=date(2018,8,20)
    # test_calculate_price_rate('603706',trade_days=1,end_date=end_date)
    test_trader_log()