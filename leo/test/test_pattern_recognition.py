# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-07-01
@last modified time:2020-07-01
"""
from unittest import TestCase
from ..pattern import pattern_recognition
from ..database import security_min_price_cn_service_impl
from ..tools import plot_tools

import numpy as np
from sqlalchemy import create_engine


class TestPatternRecognition(TestCase):
    def test_get_local_high_low_point(self):
        days = 100
        price = 10
        prices = []
        for i in range(days):#模拟A股市场
            day_rtn = np.random.rand() * 0.1
            if np.random.randint(1, 3) == 1:
                day_rtn *= -1
            price = price * day_rtn + price
            prices.append(price)
        x = np.arange(1, days+1)

        high_low_points, h_l_index, latest_flag = pattern_recognition.get_local_high_low_point(prices, 0.1)
        h_l=np.vstack(([h_l_index],[high_low_points])) #np.concatenate(([h_l_index],[high_low_points]),axis=0).transpose()
        prices_scatter=np.vstack(([x],[np.array(prices)]))
        print(h_l_index)
        print(prices)

        score=pattern_recognition.cal_local_high_low_point_score(high_low_points[-10:])
        print('score:{}'.format(score))
        plot_tools.plot_multi_y([h_l],['price'],[prices_scatter],['day_price'])

