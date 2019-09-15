# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2018-10-10
@last modified time:2018-10-10
@description: 用于聚宽回测止盈止损策略
"""
import abc, six
from jqlib.technical_analysis import *


@six.add_metaclass(abc.ABCMeta)
class IBotSeller():
    """
    基于聚宽分钟(及tick)回测框架计算止盈止损接口,在分钟回测中使用self.handle_data(),在tick回测中使用self.handle_tick()两者只能二选一
    """

    @abc.abstractmethod
    def before_market_open(self, context):
        """
        在开盘之前执行
        :param context:
        :return:
        """
        pass

    @abc.abstractmethod
    def after_market_close(self, context):
        """
        在收盘之后执行
        ps:在此函数中需要执行一遍self._eval()是因为handle_data只执行到14:59就结束，收盘的数据15:00需要再次计算
        :param context:
        :return:
        """
        pass

    @abc.abstractmethod
    def handle_data(self, context, data):
        """
        在盘中(handle_data)执行
        :param context:
        :param data:
        :return:{True:卖出,False:继续持仓}
        """
        pass

    @abc.abstractmethod
    def handle_tick(self, context, tick):
        """
        在盘中(handle_tick)执行
        :param context:
        :param tick:
        :return:{True:卖出,False:继续持仓}
        """
        pass

    @abc.abstractmethod
    def sell_reason(self):
        """
        用于打印触发卖出的条件（方便测试）
        :return:
        """
        pass


class MonkeySeller(IBotSeller):
    """
    止盈止损策略
    """

    def __init__(self, code, buy_price, volume, stop_loss=0.03, moving_stop_loss=0.015):
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
        self._stop_loss_price = (1 - stop_loss) * buy_price
        self._moving_stop_loss = 1 - moving_stop_loss  # 节省计算时间

        # ---------end init value--------------------

        self._high = 0  # 自买入后经历的最高价
        self._today_high = 0
        self._today_high_time = '09:30:00'  # 监控当天最高价的时刻
        self._current_price = buy_price
        # self._k_bar = k_bar_util.K_Bar(time_step=2)
        self._is_limit_up = False  # 是否涨停
        self._limit_up_price = 0
        self._pre_bar = None  # 上一次交易日的K线数据，至少包含[open,close,high,low,vol,amount]，多余属性暂且不管
        self._prediction_data = None  # gru模型预测的数据(该数据由另外一个程序生成，为避免其出错在使用时需要判断None)

        self._sell_reason = None  # 触发卖出的原因
        # ---------end set value-------------------

        if code.startswith('60'):  # 以60开头的为沪市
            self._code_symbol = self._code + '.XSHG'
        else:  # 以000开头的为深市
            self._code_symbol = self._code + '.XSHE'

    def before_market_open(self, context):
        self._today_high_time = '09:30:00'  # 开盘集合竞价结束开始连续竞价交易时刻
        self._today_high = 0

    def after_market_close(self, context):
        """
        每天收盘后更新数据作为明天的历史K数据,必须在每日收盘后执行一遍
        :param context: 暂时必须包含['close','high','low']
        :return:
        """
        self._pre_bar = get_price(self._code, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                    skip_paused=True,
                    count=1).iloc[0]
        self._limit_up_price = calculate_limit_up(self._pre_bar['close'])

    def handle_data(self, context, data):
        return self.check_sell(price=data[self._code_symbol].close, check_time=context.current_dt.strftime('HH:MM:SS'))

    def handle_tick(self, context, tick):
        return self.check_sell(price=tick.current, check_time=context.current_dt.strftime('HH:MM:SS'))

    def sell_reason(self):
        return self._sell_reason

    def check_sell(self, price, check_time):
        """
        是否符合卖出条件
        :param price:
        :param check_time: hh:mm:ss
        :return:
        """
        self._current_price = price
        if self._high < self._current_price:
            self._high = self._current_price

        if self._today_high < self._current_price:
            self._today_high = self._current_price
            self._today_high_time = check_time

        # self._k_bar.add_tick(tick_data) #不是tick回测时暂时不需要

        if self._strategy_stop_loss():
            return True
        # if self._strategy_cross_down_yestoday_low():
        #     return True
        if self._strategy_moving_stop_loss():
            return True
        return False

    def _strategy_stop_loss(self):
        """
        低于止损价直接卖出
        :return:
        """
        if self._current_price < self._stop_loss_price:
            self._sell_reason = '低于止损价' + str(self._stop_loss_price)
            return True
        return False

    def _strategy_cross_down_yestoday_low(self):
        """突破昨日最低价直接卖出"""
        if self._current_price < self._pre_bar['low']:
            self._sell_reason = '突破昨日最低价' + str(self._pre_bar['low'])
            return True
        return False

    def _strategy_moving_stop_loss(self):
        """移动止损"""
        if self._current_price / self._buy_price > 1.015:  # 当超过1.5个点的收益时
            if self._current_price / self._high < self._moving_stop_loss:
                self._sell_reason = '移动止损从最高价' + str(self._high) + '下降' + str(round((1-self._moving_stop_loss)*100)) + '个百分点'
                return True
        return False

    def _strategy_high_time_limit(self, check_time, estimation_breakout_seconds):
        """
        TODO
        快速拉升(区分无量还是放量)在高点达到预定的收益时如果在预定时间内还未突破则卖出
        :param check_time:
        :param estimation_breakout_seconds:预计突破时间
        :return:
        """
        breakout_seconds = self.__time_delta(check_time, self._today_high_time)
        if breakout_seconds > estimation_breakout_seconds:
            return True
        return False

    def _strategy_limit_up(self):
        """
        TODO
        涨停时的策略
        :return:
        """
        pass

    def _strategy_to_4(self):
        """
        日涨幅0-4个点时的策略
        TODO
        :return:
        """
        pass

    def _strategy_4_to_7(self):
        """
        日涨幅4-7个点时的策略
        TODO
        :return:
        """
        pass

    def _strategy_7_to_10(self):
        """
        日涨幅7-10个点时的策略
        TODO
        :return:
        """
        pass

    def __time_delta(self, a, b):
        """
        时间间隔second
        :param a: xx:xx:xx
        :param b: xx:xx:xx
        :return: a-b
        """
        seconds = int(a[0:2]) - int(b[0:2])
        seconds *= 60
        seconds += int(a[3:5]) - int(b[3:5])
        seconds *= 60
        seconds += int(a[6:]) - int(b[6:])
        return seconds


# =====================辅助函数===========================================================
def calculate_limit_up(price):
    """
    10%的增长，小数点第三位四舍五入（排除st 5%的设定）
    :param price:
    :return:
    """
    price *= 1.1
    return round(price, 2)

