# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-07-01
@last modified time:2020-07-01
"""


def get_local_high_low_point(prices, pnl_threshold):
    """
    计算局部最高最低点
    :param prices:
    :param pnl_threshold: 趋势阈值
    :return:
    """
    if len(prices) == 0:
        return None, None, None

    pnl_threshold_up = 1 + pnl_threshold
    pnl_threshold_down = 1 - pnl_threshold
    high = prices[0]
    low = prices[0]
    high_i = 0
    low_i = 0
    flag = 0  # 1:当前最高点，0：初始化，-1：当前最低点
    rs = []
    rs_index = []
    for i in range(len(prices)):
        v = prices[i]
        if flag == 0:
            if v > high:
                high = v
                high_i = i
                if high / low > pnl_threshold_up:
                    rs_index.append(low_i)
                    rs_index.append(high_i)
                    rs.append(low)
                    rs.append(high)
                    flag = 1
                    low = high
            elif v < low:
                low = v
                low_i = i
                if low / high < pnl_threshold_down:
                    rs_index.append(high_i)
                    rs_index.append(low_i)
                    rs.append(high)
                    rs.append(low)
                    flag = -1
                    high = low
        elif flag == 1:
            if v > high:  # update current high
                high = v
                low = v
                rs_index[-1] = i
                rs[-1] = v
            elif v < low:
                low = v
                if low / high < pnl_threshold_down:
                    rs_index.append(i)
                    rs.append(low)
                    flag = -1
                    high = low
        elif flag == -1:
            if v < low:
                low = v
                high = v
                rs_index[-1] = i
                rs[-1] = v
            elif v > high:
                high = v
                if high / low > pnl_threshold_up:
                    rs_index.append(i)
                    rs.append(high)
                    flag = 1
                    low = high

    return rs, rs_index, flag


def cal_local_high_low_point_score_1(high_low_points):
    """

    :param high_low_points:
    :return:
    """
    score = 0
    if len(high_low_points) <= 1:
        return score
    for i in range(1, len(high_low_points)):
        score_i = 0
        for j in range(0, i):
            if high_low_points[i] >= high_low_points[j]:
                score_i += (1.0 / (i - j))
            else:
                score_i -= (1.0 / (i - j))

        score_i /= (1.0 * i)
        score += score_i
    return score * 1.0 / (len(high_low_points) - 1)


def cal_local_high_low_point_score(high_low_points):
    """

    :param high_low_points:
    :return:
    """
    score = 0
    if len(high_low_points) <= 1:
        return score
    for i in range(1, len(high_low_points)):
        score_i = 0
        for j in range(0, i):
            if high_low_points[i] >= high_low_points[j]:
                score_i += (1.0 / (i - j))
            else:
                score_i -= (1.0 / (i - j))

        score_i /= (1.0 * i)
        score += score_i
    return score * 1.0 / (len(high_low_points) - 1)


def is_wave_raise_up_normal(prices):
    """
    主升浪模式
    :param prices: 按时间降序
    :return:
    """
    if len(prices) < 2:
        return False
    elif len(prices) == 2:
        if prices[0] > prices[1]:
            return True
        else:
            return False
    elif len(prices) == 3:
        if prices[0] < prices[1] and prices[0] > prices[2]:
            return True
        else:
            return False
    for i in range(0, len(prices) - 2, 2):
        if prices[i] < prices[i + 2] or prices[i + 1] < prices[i + 3]:
            return False

    return True

def is_wave_raise_up(prices):
    """
    主升浪模式
    :param prices: 按时间降序
    :return:
    """
    if len(prices) < 2:
        return False
    elif len(prices) == 2:
        if prices[0] > prices[1]:
            return True
        else:
            return False
    elif len(prices) == 3:
        if prices[0] < prices[1] and prices[0] > prices[2]:
            return True
        else:
            return False
    else:
        if prices[0]>prices[1]:
            return False
    for i in range(0, len(prices) - 2, 2):
        if prices[i] < prices[i + 2] or prices[i + 1] < prices[i + 3]:
            return False

    return True