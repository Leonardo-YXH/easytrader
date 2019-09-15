# -*- coding:utf-8 -*-

import tushare as ts
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import date, timedelta, datetime, time
import matplotlib.pyplot as plt
from . import k_bar_util, market_trader_util

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
    1.排除几类stock不作考虑：[ST,从当前日期往前停牌超过10天]
    2.遇到除权除息日需重新加载(移除之前的实例，重新加载持仓信息，回测使用前复权数据则不存在此情形)
    3.回测时是在下单后即开始创建实例监控，实盘则是第二天开盘前扫描持仓创建实例监控
    """

    def __init__(self, code, buy_price, volume, stop_loss=0.03, moving_stop_loss=0.015,is_backtest=False):
        """

        :param code:
        :param buy_price:
        :param volume:
        :param stop_loss:
        :param moving_stop_loss:
        """
        self._code = code
        self._buy_price = buy_price
        self._volume = volume
        self._stop_loss_price = (1 - stop_loss)*buy_price
        self._moving_stop_loss = 1 - moving_stop_loss  # 节省计算时间

        # ---------end init value--------------------

        self._high = 0  # 自买入后经历的最高价
        self._today_high = 0
        self._today_high_time = '09:30:00'  # 监控当天最高价的时刻
        self._current_price = buy_price
        self._k_bar = k_bar_util.K_Bar(time_step=2)
        self._is_limit_up = False  # 是否涨停
        self._limit_up_price = 0
        self._pre_bar = None  # 上一次交易日的K线数据，至少包含[open,close,high,low,vol,amount]，多余属性暂且不管
        self._prediction_data = None  # gru模型预测的数据(该数据由另外一个程序生成，为避免其出错在使用时需要判断None)

        # ---------end set value-------------------

        if code.startswith('60'):  # 以60开头的为沪市
            self._code_symbol = self._code + '.SH'
        else:  # 以000开头的为深市
            self._code_symbol = self._code + '.SZ'

        if not is_backtest:
            self._init_previous_data()

    def _init_previous_data(self):
        """初始化上一个交易日数据（且不是停牌数据），如果超过10天都没数据则置空（除非ST或者特殊情况比如中兴贸易战，否则停牌一般不会超过10天）"""
        pro = ts.pro_api()
        previous_trade_day = date.today() - timedelta(days=10)
        previous_trade_day = previous_trade_day.strftime('%Y%m%d')
        now = datetime.now()
        if now.hour >= 15:  # 如果是收盘后执行的话pro.daily()取到的是今天的数据，所以截止日期减去一天
            end_date = date.today() - timedelta(days=1)
        else:
            end_date = date.today()
        data = pro.daily(ts_code=self._code_symbol, start_date=previous_trade_day, end_date=end_date.strftime('%Y%m%d'))
        for _, item in data.iterrows():
            if item['vol'] != 0:
                self._pre_bar = item
                break
            else:
                continue

        self._limit_up_price = market_trader_util.calculate_limit_up(self._pre_bar['close'])

        self._high = self._pre_bar['high']


    def update_prediction_data_before_market(self, data):
        """每日开盘前更新预测数据，结构如下：
        [index,code,base_price,delta,today_open,today_close,today_high,today_low,tomorrow_open,tomorrow_close,tomorrow_high,tomorrow_low,buy_flag
        3321,601606,8.5,0.2067558914422989,17.360933303833008,17.629005432128906,18.00069236755371,16.892925262451172,19.16051483154297,19.445053100585938,20.385637283325195,18.133642196655273,1]
        :param data:每日预测数据，csv文件读取"""
        prediction_data = data[data.code == self._code]
        if not prediction_data.empty:
            self._prediction_data = prediction_data.iloc[0]

        self._today_high_time = '09:30:00'  # 开盘集合竞价结束开始连续竞价交易时刻
        self._today_high = 0

    def update_prediction_data_before_market_backtest(self):
        self._today_high_time = '09:30:00'  # 开盘集合竞价结束开始连续竞价交易时刻
        self._today_high = 0

    def update_today_data_as_pre_data_after_market(self):
        """
        每天收盘后更新数据作为明天的历史K数据,必须在每日收盘后执行一遍
        """
        today_tick = ts.get_realtime_quotes(self._code)
        if not today_tick.empty:
            today_tick = today_tick.loc[0]
        else:
            return
        self._pre_bar = pd.Series(
            {'open': float(today_tick['open']), 'close': float(today_tick['price']), 'high': float(today_tick['high'])
                , 'low': float(today_tick['low']), 'vol': float(today_tick['volume']) / 100,
             'amount': float(today_tick['amount'])})
        self._limit_up_price = market_trader_util.calculate_limit_up(self._pre_bar['close'])

    def update_today_data_as_pre_data_after_market_backtest(self,pre_bar):
        """
        每天收盘后更新数据作为明天的历史K数据,必须在每日收盘后执行一遍
        :param pre_bar: 暂时必须包含['close','high','low']
        :return:
        """
        # self._pre_bar = pd.Series(
        #     {'open': float(today_tick['open']), 'close': float(today_tick['price']), 'high': float(today_tick['high'])
        #         , 'low': float(today_tick['low']), 'vol': float(today_tick['volume']) / 100,
        #      'amount': float(today_tick['amount'])})

        self._pre_bar=pre_bar
        self._limit_up_price = market_trader_util.calculate_limit_up(self._pre_bar['close'])

    def check_sell(self, tick_data):
        """
        是否符合卖出条件
        :param tick_data:必须属性['price','time']
        :return:
        """
        self._current_price = float(tick_data['price'])
        if self._high < self._current_price:
            self._high = self._current_price

        if self._today_high < self._current_price:
            self._today_high = self._current_price
            self._today_high_time = tick_data['time']

        # self._k_bar.add_tick(tick_data) #不是tick回测时暂时不需要

        if self._strategy_stop_loss():
            return True
        if self._strategy_cross_down_yestoday_low():
            return True
        if self._strategy_moving_stop_loss():
            return True
        return False

    def _strategy_stop_loss(self):
        """
        低于止损价直接卖出
        :return:
        """
        if self._current_price < self._stop_loss_price:
            return True
        return False

    def _strategy_cross_down_yestoday_low(self):
        """突破昨日最低价直接卖出"""
        if self._current_price < self._pre_bar['low']:
            return True
        return False

    def _strategy_moving_stop_loss(self):
        """移动止损"""
        if self._current_price/self._buy_price>1.015:#当超过1.5个点的收益时
            if self._current_price / self._high < self._moving_stop_loss:
                # print('++++++++++++moving stop loss:buy:%s  sell:%s',(self._buy_price,self._current_price))
                return True
        return False

    def _strategy_3(self, tick_data):

        pre_close = float(tick_data['pre_close'])
        income_point = self._high / pre_close - 1
        if income_point > 0.03:
            if self._current_price < (pre_close + self._high) / 2:
                return True

        return False

    def _strategy_high_time_limit(self,tick_data,estimation_breakout_seconds):
        """
        在高点达到预定的收益时如果在预定时间内还未突破则卖出
        :param tick_data:
        :param estimation_breakout_seconds:预计突破时间
        :return:
        """
        breakout_seconds=self.__time_delta(tick_data['time'],self._today_high_time)
        if breakout_seconds>estimation_breakout_seconds:
            return True
        return False

    def _strategy_limit_up(self):
        if self._is_limit_up:
            pass

    def _strategy_7_to_10(self):
        """"""

    def __time_delta(self, a, b):
        """
        时间间隔second
        :param a: xx:xx:xx
        :param b: xx:xx:xx
        :return: a-b
        """
        seconds = float(a[0:2]) - float(b[0:2])
        seconds *= 60
        seconds += float(a[3:5]) - float(b[3:5])
        seconds *= 60
        seconds += float(a[6:]) - float(b[6:])
        return seconds


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


def get_history_money_flow_1(stock_code=None, start_date=None, end_date=None, trade_days=5, amount_threshold=100000):
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
    trade_days_count = 0
    while start_date < end_date and trade_days_count < trade_days:
        start = end_date.strftime('%Y-%m-%d')
        end_date -= timedelta(days=1)
        tick_data = ts.get_tick_data(stock_code, date=start, src='tt')
        if tick_data is None or tick_data.empty:
            continue
        trade_days_count += 1

        huge_data = tick_data[tick_data['amount'] > amount_threshold]
        buy_data = huge_data[huge_data['type'] == u'买盘']
        sell_data = huge_data[huge_data['type'] == u'卖盘']
        amount_buy += buy_data['amount'].sum()
        amount_sell += sell_data['amount'].sum()
        volume_buy += buy_data['volume'].sum()
        volume_sell += sell_data['volume'].sum()

    return [amount_buy, volume_buy, amount_sell, volume_sell]


def calculate_price_rate(stock_code=None, start_date=None, end_date=None, trade_days=5, amount_threshold=100000,
                         price=1):
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
    rs = get_history_money_flow_1(stock_code=stock_code, start_date=start_date, end_date=end_date,
                                  trade_days=trade_days, amount_threshold=amount_threshold)
    expect_price = (rs[0] - rs[2]) / (rs[1] - rs[3])
    expect_price /= 100.0
    rate = expect_price / price
    if rs[1] > rs[3]:
        if rs[0] > rs[2]:
            return expect_price, 1000 + rate
        else:
            return expect_price, 10000 - rate
    else:
        if rs[0] > rs[2]:
            return expect_price, -rate
        else:
            return expect_price, 900 + rate


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
    x1 = [0, 1, 2, 3, 4, 5]
    x2 = [0.4, 1.4, 2.4, 3.4, 4.4, 5.4]
    amount_sell = sum([money_flow.level1_amount_sell, money_flow.level2_amount_sell, money_flow.level3_amount_sell,
                       money_flow.level4_amount_sell, money_flow.level5_amount_sell])
    amount_buy = sum([money_flow.level1_amount_buy, money_flow.level2_amount_buy, money_flow.level3_amount_buy,
                      money_flow.level4_amount_buy, money_flow.level5_amount_buy])
    y1 = [money_flow.level1_amount_sell, money_flow.level2_amount_sell, money_flow.level3_amount_sell,
          money_flow.level4_amount_sell, money_flow.level5_amount_sell, amount_sell]
    y2 = [money_flow.level1_amount_buy, money_flow.level2_amount_buy, money_flow.level3_amount_buy,
          money_flow.level4_amount_buy, money_flow.level5_amount_buy, amount_buy]
    volume_sell = sum([money_flow.level1_volume_sell, money_flow.level2_volume_sell, money_flow.level3_volume_sell,
                       money_flow.level4_volume_sell, money_flow.level5_volume_sell])
    volume_buy = sum([money_flow.level1_volume_buy, money_flow.level2_volume_buy, money_flow.level3_volume_buy,
                      money_flow.level4_volume_buy, money_flow.level5_volume_buy])
    z1 = [money_flow.level1_volume_sell, money_flow.level2_volume_sell, money_flow.level3_volume_sell,
          money_flow.level4_volume_sell, money_flow.level5_volume_sell, volume_sell]
    z2 = [money_flow.level1_volume_buy, money_flow.level2_volume_buy, money_flow.level3_volume_buy,
          money_flow.level4_volume_buy, money_flow.level5_volume_buy, volume_buy]
    m1 = [money_flow.level1_amount_sell / money_flow.level1_volume_sell,
          money_flow.level2_amount_sell / money_flow.level2_volume_sell,
          money_flow.level3_amount_sell / money_flow.level3_volume_sell,
          money_flow.level4_amount_sell / (money_flow.level4_volume_sell + 0.001),
          money_flow.level5_amount_sell / (money_flow.level5_volume_sell + 0.001),
          amount_sell / volume_sell]
    m2 = [money_flow.level1_amount_buy / money_flow.level1_volume_buy,
          money_flow.level2_amount_buy / money_flow.level2_volume_buy,
          money_flow.level3_amount_buy / money_flow.level3_volume_buy,
          money_flow.level4_amount_buy / (money_flow.level4_volume_buy + 0.001),
          money_flow.level5_amount_buy / (money_flow.level5_volume_buy + 0.001),
          amount_buy / volume_buy]

    fig = plt.figure()
    ax1 = fig.add_subplot(211)
    ax1.bar(x1, y1, 0.4, color='green')
    ax1.bar(x2, y2, 0.4, color='red', label=u'成交额')

    ax2 = ax1.twinx()
    plt.plot(x1, m1, 'yo')
    plt.plot(x2, m2, 'yo')

    ax3 = fig.add_subplot(212)
    ax3.bar(x1, z1, 0.4, color='green')
    ax3.bar(x2, z2, 0.4, color='red', label=u'成交量')

    plt.show()


def test_calculate_price_rate(stock_code='000001', trade_days=5, end_date=None):
    # end_date=date.today()
    start_date = end_date - timedelta(days=15)
    realtime_tick = ts.get_realtime_quotes(stock_code)
    price = float(realtime_tick['price'].iat[0])
    expect_price, rate = calculate_price_rate(stock_code, start_date, end_date, trade_days, amount_threshold=100000,
                                              price=price)
    print(expect_price, rate)


def test_trader_log():
    import logging
    log = logging.getLogger('trader')
    log.info('buy 100 vol at price 4.5')


if __name__ == '__main__':
    start_date = date.today() - timedelta(days=0)
    # money_flow = get_history_money_flow('002925', start_date=start_date, end_date=date.today()+timedelta(days=1))
    # money_flow = get_today_money_flow('002236')
    # draw_money_flow_by_pie(money_flow)
    # draw_money_flow_by_bar(money_flow)
    # print(money_flow.volume)
    # end_date=date(2018,8,20)
    # test_calculate_price_rate('603706',trade_days=1,end_date=end_date)
    # test_trader_log()
    # ts.set_token('3191ba2281dd651a0a3e3da586d78903bd05a2881e283058e4e8194e')
    # pro=ts.pro_api()
    # df = pro.daily(ts_code='000001.SZ', start_date='20180701', end_date='20180718')
    # print(df)
