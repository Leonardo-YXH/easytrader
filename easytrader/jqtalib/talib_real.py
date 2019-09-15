# coding:utf-8
"""
@author: leonardo
@created time: 2018-09-28
@last modified time:2018-10-10
"""
import abc, six, math
from jqlib.technical_analysis import *
from jqdata import *


@six.add_metaclass(abc.ABCMeta)
class IQuant():
    """
    基于聚宽分钟(及tick)回测框架计算日线的实时指标接口,在分钟回测中使用self.handle_data(),在tick回测中使用self.handle_tick()两者只能二选一
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
        :return:
        """
        pass

    @abc.abstractmethod
    def handle_tick(self, context, tick):
        """
        在盘中(handle_tick)执行
        :param context:
        :param tick:
        :return:
        """
        pass

    @abc.abstractmethod
    def value(self):
        """
        返回指标
        :return:
        """
        pass

    @abc.abstractmethod
    def check(self):
        """
        决定是否买卖
        {negative:sell;0:none;positive:buy}
        :return:
        """
        pass

    @abc.abstractmethod
    def to_string(self):
        """
        用于打印指标（方便测试）
        :return:
        """
        pass


class KD_Real(IQuant):
    """
    RSV:=(CLOSE-LLV(LOW,N))/(HHV(HIGH,N)-LLV(LOW,N))*100;
    K:SMA(RSV,M1,1);
    D:SMA(K,M2,1);
    """

    def __init__(self, security, N=5, M1=3, M2=3):
        self._value = {}
        self._security = security
        self._N = N
        self._M1 = M1
        self._M2 = M2

        self._value['K'] = None
        self._value['D'] = None

        self._rate = 1 + 0.015 * N  # 假定在过去(N*2-1)个交易日最高最低价超过一定比率

    def before_market_open(self, context):
        if self._value['K'] is None:  # first init
            K_, D_ = KD([self._security], check_date=context.previous_date.strftime('%Y-%m-%d'), N=self._N, M1=self._M1,
                        M2=self._M2)
            self._value['K_'] = K_[self._security]
            self._value['D_'] = D_[self._security]
        else:  # update today data as previous data
            self._value['K_'] = self._value['K']
            self._value['D_'] = self._value['D']
        self._previous_date = context.previous_date.strftime('%Y-%m-%d')
        # 由于存在复权，hhv和llv可能会有所改变，所以需要每天重新初始化
        bars = get_price(self._security, end_date=self._previous_date, frequency='1d',
                         fields=['high', 'low', 'close'], skip_paused=True, count=self._N - 1)
        self._value['hhv'] = max(bars['high'])
        self._value['llv'] = min(bars['low'])

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close, close, close)

    def handle_data(self, context, data):
        self._eval(high=data[self._security].high, low=data[self._security].low, close=data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current, tick.current, tick.current)

    def _eval(self, high, low, close):
        self._current_price = close
        if high > self._value['hhv']:
            self._value['hhv'] = high
        elif low < self._value['llv']:
            self._value['llv'] = low
        rsv = 100.0 * (close - self._value['llv']) / (self._value['hhv'] - self._value['llv'])
        self._value['K'] = (rsv + (self._M1 - 1) * self._value['K_']) / self._M1
        self._value['D'] = (self._value['K'] + (self._M2 - 1) * self._value['D_']) / self._M2

    def value(self):
        return self._value

    def check(self):
        if self._value['K_'] < self._value['D_']:
            if self._value['K'] > self._value['D']:  # 金叉
                return 1
                # bars = get_price(self._security, end_date=self._previous_date, frequency='1d',
                #                  fields=['high', 'low'], skip_paused=True, count=(self._N * 2 - 1))
                # hhv = max(bars['high'])
                # llv = min(bars['low'])
                # if hhv / llv >= self._rate and self._current_price < (hhv + llv) / 2.0:
                #     return 1
        elif self._value['K_'] > self._value['D_']:
            if self._value['K'] < self._value['D']:  # 死叉
                return -1
        return 0

    def to_string(self):
        return '{K:' + str(self._value['K']) + '    D:' + str(self._value['D']) + '}'


class SKDJ_Real(IQuant):
    """
    LOWV:=LLV(LOW,N);
    HIGHV:=HHV(HIGH,N);
    RSV:=EMA((CLOSE-LOWV)/(HIGHV-LOWV)*100,M);#区别于KD指标，该指标更平滑
    K:EMA(RSV,M);
    D:MA(K,M);
    """

    def __init__(self, security, N=5, M=3):
        self._value = {}
        self._security = security
        self._N = N
        self._M = M

        self._value['K'] = None
        self._value['D'] = None

        alpha = 2.0 / (M + 1)
        self._need_N = int(math.log(0.00001 / alpha, 1 - alpha))

    def before_market_open(self, context):
        self._previous_date = context.previous_date.strftime('%Y-%m-%d')
        if self._value['K'] is None:  # first init
            trade_days = get_trade_days(end_date=context.previous_date, count=self._M - 1)
            self._K_list = []
            for day in trade_days:
                K_, D_ = SKDJ([self._security], check_date=day.strftime('%Y-%m-%d'), N=self._N, M=self._M)
                self._K_list.append(K_[self._security])
            self._value['K_'] = K_[self._security]
            self._value['D_'] = D_[self._security]

            self._rsv_list = []
            tmp_bars = get_price(self._security, end_date=self._previous_date, frequency='1d',
                                 fields=['high', 'low', 'close'], skip_paused=True,
                                 count=self._need_N + self._M + self._N - 2)
            highs = tmp_bars['high']
            lows = tmp_bars['low']
            closes = tmp_bars['close']
            tmp_rsv_list = []
            for i in range(self._need_N + self._M - 1):
                lowv = min(lows[i:i + self._N])
                highv = max(highs[i:i + self._N])
                tmp_rsv_list.append(100 * (closes[i + self._N - 1] - lowv) / (highv - lowv))
            for i in range(self._M - 1):
                self._rsv_list.append(sma_cn(tmp_rsv_list[i:i + self._need_N + 1], n=self._M + 1, m=2))

        else:  # update today data as previous data
            self._value['K_'] = self._value['K']
            self._value['D_'] = self._value['D']

        # 由于存在复权，hhv和llv可能会有所改变，所以需要每天重新初始化
        bars = get_price(self._security, end_date=self._previous_date, frequency='1d',
                         fields=['high', 'low'], skip_paused=True, count=self._N - 1)
        self._value['hhv'] = max(bars['high'])
        self._value['llv'] = min(bars['low'])
        self._sum_k = sum(self._K_list)

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close, close, close)

        self._rsv_list.pop(0)
        self._rsv_list.append(self._rsv)
        self._K_list.pop(0)
        self._K_list.append(self._value['K'])

    def handle_data(self, context, data):
        self._eval(high=data[self._security].high, low=data[self._security].low, close=data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current, tick.current, tick.current)

    def _eval(self, high, low, close):
        self._current_price = close
        if high > self._value['hhv']:
            self._value['hhv'] = high
        elif low < self._value['llv']:
            self._value['llv'] = low
        self._rsv = (self._rsv_list[-1] * (self._M - 1) + 200.0 * (close - self._value['llv']) / (
                self._value['hhv'] - self._value['llv'])) / (self._M + 1)

        self._value['K'] = (self._rsv * 2 + (self._M - 1) * self._value['K_']) / (self._M + 1)
        self._value['D'] = (self._sum_k + self._value['K']) / self._M

    def value(self):
        return self._value

    def check(self):
        if self._value['K_'] < self._value['D_']:
            if self._value['K'] > self._value['D']:  # 金叉
                return 1
        elif self._value['K_'] > self._value['D_']:
            if self._value['K'] < self._value['D']:  # 死叉
                return -1
        return 0

    def to_string(self):
        return '{K:' + str(self._value['K']) + '    D:' + str(self._value['D']) + '}'


class MACD_Real(IQuant):
    """
    DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
    DEA:EMA(DIF,MID);
    MACD:(DIF-DEA)*2
    """

    def __init__(self, security, short=12, long=26, mid=9):
        self._value = {}

        self._security = security
        self._short = short
        self._long = long
        self._mid = mid

        self._value['dif'] = None
        self._value['dea'] = None
        self._value['macd'] = None

    def before_market_open(self, context):

        if self._value['dif'] is None:
            self._value['short_ema_'] = \
                EMA([self._security], check_date=context.previous_date.strftime('%Y-%m-%d'), timeperiod=self._short)[
                    self._security]
            self._value['long_ema_'] = EMA([self._security], check_date=context.previous_date.strftime('%Y-%m-%d'),
                                           timeperiod=self._long)[self._security]
            dif, dea, macd = MACD([self._security], check_date=context.previous_date.strftime('%Y-%m-%d'),
                                  SHORT=self._short, LONG=self._long, MID=self._mid)
            self._value['dif_'] = dif[self._security]
            self._value['dea_'] = dea[self._security]
        else:  # 以下四个参数与close是线性关系，所以复权后也不会改变，可以直接使用
            self._value['short_ema_'] = self._value['short_ema']
            self._value['long_ema_'] = self._value['long_ema']
            self._value['dif_'] = self._value['dif']
            self._value['dea_'] = self._value['dea']

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close)

    def handle_data(self, context, data):
        self._eval(data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current)

    def _eval(self, close):
        self._value['short_ema'] = (2 * close + (self._short - 1) * self._value['short_ema_']) / (
                self._short + 1.0)
        self._value['long_ema'] = (2 * close + (self._long - 1) * self._value['long_ema_']) / (
                self._long + 1.0)
        self._value['dif'] = self._value['short_ema'] - self._value['long_ema']
        self._value['dea'] = (2 * self._value['dif'] + (self._mid - 1) * self._value['dea_']) / (self._mid + 1.0)
        self._value['macd'] = 2 * (self._value['dif'] - self._value['dea'])

    def value(self):
        return self._value

    def check(self):
        if self._value['dif_'] < self._value['dea_']:
            if self._value['dif'] > self._value['dea']:  # 金叉
                return 1
        elif self._value['dif_'] > self._value['dea_']:
            if self._value['dif'] < self._value['dea']:  # 死叉
                return -1
        return 0

    def to_string(self):
        return '{dif:' + str(self._value['dif']) + '    dea:' + str(self._value['dea']) + '    macd:' + str(
            self._value['macd']) + '}'


class RSI_Real(IQuant):
    """
    LC:=REF(CLOSE,1);
    RSI1:SMA(MAX(CLOSE-LC,0),N1,1)/SMA(ABS(CLOSE-LC),N1,1)*100;
    RSI2:SMA(MAX(CLOSE-LC,0),N2,1)/SMA(ABS(CLOSE-LC),N2,1)*100;
    RSI3:SMA(MAX(CLOSE-LC,0),N3,1)/SMA(ABS(CLOSE-LC),N3,1)*100;
    """

    def __init__(self, security, N1=6, N2=12, N3=24):
        self._value = {}

        self._security = security
        self._N1 = N1
        self._N2 = N2
        self._N3 = N3

        self._max_N = self.__calculate_max_n(max(N1, N2, N3))
        self._need_N1 = self.__calculate_max_n(N1)
        self._need_N2 = self.__calculate_max_n(N2)
        self._need_N3 = self.__calculate_max_n(N3)

        self._value['rsi1'] = None

    def before_market_open(self, context):
        if self._value['rsi1'] is None:
            previous_date = context.previous_date.strftime('%Y-%m-%d')
            tmp = RSI([self._security], check_date=previous_date, N1=self._N1)
            self._value['rsi1_'] = tmp[self._security]
            tmp = RSI([self._security], check_date=previous_date, N1=self._N2)
            self._value['rsi2_'] = tmp[self._security]
            tmp = RSI([self._security], check_date=previous_date, N1=self._N3)
            self._value['rsi3_'] = tmp[self._security]
        else:
            self._value['rsi1_'] = self._value['rsi1']
            self._value['rsi2_'] = self._value['rsi2']
            self._value['rsi3_'] = self._value['rsi3']
        # 可能存在复权，get_price的数据不能用来缓存计算（也可以通过上一个收盘价和当天取到的收盘价比较是否存在复权，这里为了简化代码（偷懒）直接重新拉取数据）
        self._X = \
            get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                      fields=['close'], skip_paused=True, count=self._max_N)['close']
        self._lc = self._X[-1]
        self._max_X, self._abs_X = self.__cumminus(self._X)
        # 今日值的占位符
        self._max_X.append(0)
        self._abs_X.append(0)

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close)

    def handle_data(self, context, data):
        self._eval(data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current)

    def _eval(self, close):
        dx = close - self._lc
        if dx > 0:
            self._abs_X[-1] = dx
            self._max_X[-1] = dx
        else:
            self._abs_X[-1] = -dx
            self._max_X[-1] = 0

        max_sma = sma_cn(X=self._max_X[-self._need_N1:], n=self._N1, m=1)
        abs_sma = sma_cn(X=self._abs_X[-self._need_N1:], n=self._N1, m=1)
        self._value['rsi1'] = 100.0 * max_sma / abs_sma

        max_sma = sma_cn(X=self._max_X[-self._need_N2:], n=self._N2, m=1)
        abs_sma = sma_cn(X=self._abs_X[-self._need_N2:], n=self._N2, m=1)
        self._value['rsi2'] = 100.0 * max_sma / abs_sma

        max_sma = sma_cn(X=self._max_X[-self._need_N3:], n=self._N3, m=1)
        abs_sma = sma_cn(X=self._abs_X[-self._need_N3:], n=self._N3, m=1)
        self._value['rsi3'] = 100.0 * max_sma / abs_sma

    def value(self):
        return self._value

    def check(self):
        if self._value['rsi1_'] < self._value['rsi2_']:
            if self._value['rsi1'] > self._value['rsi2']:  # 金叉
                return 1
        elif self._value['rsi1_'] > self._value['rsi2_']:
            if self._value['rsi1'] < self._value['rsi2']:  # 死叉
                return -1
        return 0

    def __cumminus(self, X):
        rs_max = []
        rs_abs = []
        for i in range(len(X) - 1):
            dx = X[i + 1] - X[i]
            if dx > 0:
                rs_abs.append(dx)
                rs_max.append(dx)
            else:
                rs_abs.append(-dx)
                rs_max.append(0)
        return rs_max, rs_abs

    def __calculate_max_n(self, n, theta=0.00001):
        """
        计算需要迭代的次数，保证最后的叠加量不超过theta
        :param n:
        :param theta:
        :return:
        """
        alpha = 1.0 / n
        beta = 1 - alpha
        return int(math.log(theta / alpha, beta))

    def to_string(self):
        return '{rsi1:' + str(self._value['rsi1']) + '    rsi2:' + str(self._value['rsi2']) + '    rsi3:' + str(
            self._value['rsi3']) + '}'


class ROC_Real(IQuant):
    """
    ROC:100*(CLOSE-REF(CLOSE,N))/REF(CLOSE,N);
    MAROC:MA(ROC,M);
    """

    def __init__(self, security, N=12, M=6):
        self._value = {}

        self._security = security
        self._N = N
        self._M = M

        self._roc_list = None

    def before_market_open(self, context):
        if self._roc_list is None:
            bars = get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                             fields=['close'], skip_paused=True, count=(self._N + self._M - 1))['close']
            self._lc = bars[-self._N]
            self._roc_list = map(lambda x, y: 100 * (y / x - 1), bars[:self._M - 1], bars[self._N:])
        else:
            self._lc = get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                                 fields=['close'], skip_paused=True, count=self._N)['close'][0]
        self._sum_roc = sum(self._roc_list)

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close)
        self._roc_list.pop(0)
        self._roc_list.append(self._value['roc'])

    def handle_data(self, context, data):
        self._eval(data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current)

    def _eval(self, close):
        self._value['roc'] = 100 * (close / self._lc - 1)
        self._value['maroc'] = (self._sum_roc + self._value['roc']) / self._M

    def value(self):
        return self._value

    def check(self):
        # TODO
        return 0

    def to_string(self):
        return '{roc:' + str(self._value['roc']) + '   maroc:' + str(self._value['maroc']) + '}'


class MA_Real(IQuant):
    """
    收盘价均线
    """

    def __init__(self, security, M1=5, M2=10, M3=20, M4=60):
        self._value = {}

        self._security = security
        self._M1 = M1
        self._M2 = M2
        self._M3 = M3
        self._M4 = M4

        self._max_M = max(M1, M2, M3, M4)

        self._value['ma1'] = None

    def before_market_open(self, context):
        if self._value['ma1'] is None:
            self._list = list(
                get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=self._max_M - 1)['close'])
        self._sum1 = sum(self._list[-self._M1 + 1:])
        self._sum2 = sum(self._list[-self._M2 + 1:])
        self._sum3 = sum(self._list[-self._M3 + 1:])
        self._sum4 = sum(self._list[-self._M4 + 1:])

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close)

        self._list.pop(0)
        self._list.append(close)

    def handle_data(self, context, data):
        self._eval(data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current)

    def _eval(self, close):
        self._value['ma1'] = (self._sum1 + close) / self._M1
        self._value['ma2'] = (self._sum2 + close) / self._M2
        self._value['ma3'] = (self._sum3 + close) / self._M3
        self._value['ma4'] = (self._sum4 + close) / self._M4

    def value(self):
        return self._value

    def check(self):
        # TODO
        return 0

    def to_string(self):
        return '{ma1:' + str(self._value['ma1']) + '    ma2:' + str(self._value['ma2']) + '    ma3:' + str(
            self._value['ma3']) + '    ma4:' + str(self._value['ma4']) + '}'


class VMA_Real(IQuant):
    """
    自定义权重均线
    VV:=(HIGH * K1 + OPEN * K2 + LOW * K3 + CLOSE * K4)/(K1+K2+K3+K4);
    VMA1:MA(VV,M1);
    VMA2:MA(VV,M2);
    """

    def __init__(self, security, M1=5, M2=10, M_HIGH=1, M_LOW=1, M_OPEN=2, M_CLOSE=2):
        self._value = {}

        self._security = security
        self._M1 = M1
        self._M2 = M2
        self._M_HIGH = M_HIGH
        self._M_LOW = M_LOW
        self._M_OPEN = M_OPEN
        self._M_CLOSE = M_CLOSE

        self._max_M = max(M1, M2)
        self._sum_M = M_OPEN + M_CLOSE + M_HIGH + M_LOW

        self._value['ma1'] = None

    def before_market_open(self, context):
        if self._value['ma1'] is None:
            bars = get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                             fields=['high', 'low', 'open', 'close'], skip_paused=True, count=self._max_M)
            vv_list = (bars['high'] * self._M_HIGH + bars['low'] * self._M_LOW + bars['open'] * self._M_OPEN + bars[
                'close'] * self._M_CLOSE) / self._sum_M
            self._value['ma1_'] = vv_list[-self._M1:].sum()
            self._value['ma2_'] = vv_list[-self._M2:].sum()
            self._vv_list = list(vv_list[1:])

        else:
            self._value['ma1_'] = self._value['ma1']
            self._value['ma2_'] = self._value['ma2']

        self._sum1 = sum(self._vv_list[-self._M1 + 1:])
        self._sum2 = sum(self._vv_list[-self._M2 + 1:])

        self._open = None
        self._high = 0
        self._low = 1000000

    def after_market_close(self, context):
        today = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close', 'open', 'high', 'low'], skip_paused=True, count=1).iloc[0]
        vv = (
                     today.high * self._M_HIGH + today.low * self._M_LOW + today.open * self._M_OPEN + today.close * self._M_CLOSE) / self._sum_M
        self._eval(today.high, today.low, today.close)

        self._vv_list.pop(0)
        self._vv_list.append(vv)

    def handle_data(self, context, data):
        if self._open is None:
            self._open = data[self._security].open

        self._eval(data[self._security].high, data[self._security].low, data[self._security].close)

    def handle_tick(self, context, tick):
        if self._open is None:
            self._open = tick.current
        self._eval(tick.current, tick.current, tick.current)

    def _eval(self, high, low, close):
        if self._high < high:
            self._high = high
        if self._low > low:
            self._low = low
        vv = (
                     self._high * self._M_HIGH + self._low * self._M_LOW + self._open * self._M_OPEN + close * self._M_CLOSE) / self._sum_M
        self._value['ma1'] = (self._sum1 + vv) / self._M1
        self._value['ma2'] = (self._sum2 + vv) / self._M2

    def value(self):
        return self._value

    def check(self):
        """
        五日线上穿十日线买进
        :return:
        """
        if self._value['ma1_'] < self._value['ma2_']:
            if self._value['ma1'] > self._value['ma2']:
                return 1
        elif self._value['ma1_'] > self._value['ma2_']:
            if self._value['ma1'] < self._value['ma2']:
                return -1
        return 0

    def to_string(self):
        return '{ma1:' + str(self._value['ma1']) + '    ma2:' + str(self._value['ma2']) + '}'


class CCI_Real(IQuant):
    """
      TYP:=(HIGH+LOW+CLOSE)/3;
      CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
      其中AVEDEV=AVG(abs(MA-TYP))
    """

    def __init__(self, security, N=14):
        self._value = {}

        self._security = security
        self._N = N

        self._value['cci'] = None

    def before_market_open(self, context):
        if self._value['cci'] is None:
            bars = get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                             fields=['close', 'high', 'low'], skip_paused=True, count=self._N - 1)
            self._typ_list = ((bars.close + bars.high + bars.low) / 3.0).tolist()

        self._typ_list.append(0)  # 占位符
        self._sum_typ = sum(self._typ_list)

        self._high = 0
        self._low = 1000000

    def after_market_close(self, context):
        today_bar = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                              fields=['close', 'high', 'low'], skip_paused=True, count=1).iloc[0]
        typ = (today_bar.close + today_bar.high + today_bar.low) / 3
        self._eval(typ)

        self._typ_list.pop(0)

    def handle_data(self, context, data):
        if self._high < data[self._security].high:
            self._high = data[self._security].high
        if self._low > data[self._security].low:
            self._low = data[self._security].low
        typ = (data[self._security].close + self._high + self._low) / 3
        self._eval(typ)

    def handle_tick(self, context, tick):
        if self._high < tick.current:
            self._high = tick.current
        if self._low > tick.current:
            self._low = tick.current
        typ = (tick.current + self._high + self._low) / 3
        self._eval(typ)

    def _eval(self, typ):
        self._typ_list[-1] = typ
        ma_typ = (self._sum_typ + typ) / self._N
        adeved = sum(map(lambda x: abs(x - ma_typ), self._typ_list)) / self._N
        self._value['cci'] = (typ - ma_typ) / (0.015 * adeved)

    def value(self):
        return self._value

    def check(self):
        """
        TODO
        1.CCI 为正值时，视为多头市场；为负值时，视为空头市场；
        2.常态行情时，CCI 波动于±100 的间；强势行情，CCI 会超出±100 ；
        3.CCI>100 时，买进，直到CCI<100 时，卖出；
        4.CCI<-100 时，放空，直到CCI>-100 时，回补。
        :return:
        """
        return 0

    def to_string(self):
        return '{cci:' + str(self._value['cci']) + '}'


class ADTM_Real(IQuant):
    """
    DTM:=IF(OPEN<=REF(OPEN,1),0,MAX((HIGH-OPEN),(OPEN-REF(OPEN,1))));
    DBM:=IF(OPEN>=REF(OPEN,1),0,MAX((OPEN-LOW),(OPEN-REF(OPEN,1))));#后面部分(OPEN-REF(OPEN,1)明显小于0，不知道通达信写这部分意义何在？
    STM:=SUM(DTM,N);
    SBM:=SUM(DBM,N);
    ADTM:IF(STM>SBM,(STM-SBM)/STM,IF(STM=SBM,0,(STM-SBM)/SBM));
    MAADTM:MA(ADTM,M);
    """

    def __init__(self, security, N=23, M=8):
        self._value = {}

        self._security = security
        self._N = N
        self._M = M

        self._adtm_list = None

    def before_market_open(self, context):
        if self._adtm_list is None:
            bars = get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                             fields=['open', 'high', 'low'], skip_paused=True, count=self._N)
            self._open_list = list(bars['open'])
            self._high_list = list(bars['high'])
            self._low_list = list(bars['low'])
            self._stm_list, self._sbm_list = self.__stm_sbm()
            trade_days = get_trade_days(end_date=context.previous_date.strftime('%Y-%m-%d'), count=self._M - 1)
            self._adtm_list = []
            for trade_day in trade_days:
                ADTM_, MAADTM = ADTM(self._security, check_date=trade_day.strftime('%Y-%m-%d'), N=self._N, M=self._M)
                self._adtm_list.append(ADTM_[self._security])
            self._value['adtm_'] = ADTM_[self._security]
            self._value['maadtm_'] = MAADTM[self._security]
        else:
            self._value['adtm_'] = self._value['adtm']
            self._value['maadtm_'] = self._value['maadtm']
        self._STM = sum(self._stm_list)
        self._SBM = sum(self._sbm_list)
        self._sum_adtm = sum(self._adtm_list)

        self._open = None
        self._high = 0
        self._low = 1000000  # 假定股价没有超过1000000

    def after_market_close(self, context):
        today_bar = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                              fields=['open', 'high', 'low'], skip_paused=True, count=1).iloc[0]
        self._eval(today_bar.high, today_bar.low, today_bar.open)

        self._stm_list.pop(0)
        self._stm_list.append(self._stm)
        self._sbm_list.pop(0)
        self._sbm_list.append(self._sbm)
        self._adtm_list.pop(0)
        self._adtm_list.append(self._adtm)
        self._high_list.pop(0)
        self._high_list.append(today_bar.high)
        self._low_list.pop(0)
        self._low_list.append(today_bar.low)
        self._open_list.pop(0)
        self._open_list.append(today_bar.open)

    def handle_data(self, context, data):
        self._eval(data[self._security].high, data[self._security].low, data[self._security].open)

    def handle_tick(self, context, tick):
        self._eval(tick.current, tick.current, tick.current)

    def _eval(self, high, low, open):
        if self._open is None:
            self._open = open
            self._dx = self._open - self._open_list[-1]
        if self._high < high:
            self._high = high
        if self._low > low:
            self._low = low

        # dx = open - self._open_list[-1]
        self._stm, self._sbm = 0, 0
        if self._dx < 0:
            self._stm = 0
            self._sbm = open - low
        elif self._dx > 0:
            self._stm = max(high - open, self._dx)
            self._sbm = 0

        STM = self._STM + self._stm
        SBM = self._SBM + self._sbm
        self._adtm = 0
        if STM > SBM:
            self._adtm = (STM - SBM) / STM
        elif STM < SBM:
            self._adtm = (STM - SBM) / SBM

        self._value['adtm'] = self._adtm
        self._value['maadtm'] = (self._sum_adtm + self._adtm) / self._M

    def value(self):
        return self._value

    def check(self):
        """
        1.ADTM指标在+1到-1之间波动。
        2.低于-0.5时为低风险区,高于+0.5时为高风险区，需注意风险。
        3.ADTM上穿ADTMMA时，买入股票；ADTM跌穿ADTMMA时，卖出股票。
        :return:
        """
        if self._value['adtm_'] < self._value['maadtm_']:
            if self._value['adtm'] > self._value['maadtm']:
                return 1
        else:
            if self._value['adtm'] < self._value['maadtm']:
                return -1
        return 0

    def __stm_sbm(self):
        stm_list = []
        sbm_list = []
        for i in range(len(self._open_list) - 1):
            dx = self._open_list[i + 1] - self._open_list[i]
            if dx < 0:
                stm_list.append(0)
                sbm_list.append(self._open_list[i + 1] - self._low_list[i + 1])
            elif dx > 0:
                stm_list.append(max(self._high_list[i + 1] - self._open_list[i + 1], dx))
                sbm_list.append(0)
            else:
                stm_list.append(0)
                sbm_list.append(0)
        return stm_list, sbm_list

    def to_string(self):
        return '{adtm:' + str(self._value['adtm']) + '    maadtm:' + str(self._value['maadtm']) + '}'


class BOLL_Real(IQuant):
    """
    BOLL:MA(CLOSE,M);
    UB:BOLL+2*STD(CLOSE,M);
    LB:BOLL-2*STD(CLOSE,M);
    """

    def __init__(self, security, M=20):
        self._security = security
        self._M = M

        self._value = {}
        self._close_list = None

    def before_market_open(self, context):
        if self._close_list is None:
            self._close_list = list(
                get_price(self._security, end_date=context.previous_date.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=self._M - 1)['close'])
        self._sum = sum(self._close_list)
        self._close_list.append(0)  # 占位符

    def after_market_close(self, context):
        close = get_price(self._security, end_date=context.current_dt.strftime('%Y-%m-%d'), frequency='1d',
                          fields=['close'], skip_paused=True, count=1)['close'][0]
        self._eval(close)

        self._close_list.pop(0)

    def handle_data(self, context, data):
        self._eval(data[self._security].close)

    def handle_tick(self, context, tick):
        self._eval(tick.current)

    def _eval(self, close):
        self._value['boll'] = (self._sum + close) / self._M
        self._close_list[-1] = close
        std = math.sqrt(sum(map(lambda x: math.pow(x - self._value['boll'], 2), self._close_list)) / (self._M - 1))
        # std=np.std(self._close_list,ddof=1)
        self._value['ub'] = self._value['boll'] + 2 * std
        self._value['lb'] = self._value['boll'] - 2 * std

    def value(self):
        return self._value

    def check(self):
        # TODO
        return 0

    def to_string(self):
        return '{boll:' + str(self._value['boll']) + '    ub:' + str(self._value['ub']) + '    lb:' + str(
            self._value['lb']) + '}'


# ==================多指标共振集合================================
class QuantFactory(object):
    """
    多指标集合
    """

    def __init__(self):
        self._factory = []

    def add(self, factor):
        self._factory.append(factor)

    def before_market_open(self, context):
        for fac in self._factory:
            fac.before_market_open(context)

    def after_market_close(self, context):
        for fac in self._factory:
            fac.after_market_close(context)

    def handle_data(self, context, data):
        for fac in self._factory:
            fac.handle_data(context, data)

    def handle_tick(self, context, tick):
        for fac in self._factory:
            fac.handle_tick(context, tick)

    def check(self):
        for fac in self._factory:
            if fac.check() <= 0:
                return False
        return True


def sma_cn(X, n, m=2):
    y = X[0]
    for i in range(1, len(X)):
        y = (m * X[i] + (n - m) * y) / n
    return y


if __name__ == '__main__':
    a = [72.80701754385962, 34.78260869565227, 31.4285714285713, 74.99999999999982, 0.0, 3.3333333333335506,
         12.903225806451603, 5.6338028169015315, 19.230769230769177, 18.918918918919037, 40.540540540540725,
         10.344827586206707, 2.3809523809523307, 90.90909090909109, 84.8484848484849, 80.8823529411766,
         97.05882352941184]
    for n in range(4, 16, 1):
        print(sma_cn(a[-n:], n=4, m=2))
