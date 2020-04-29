# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-04-29
@last modified time:2020-04-29
更新持仓信息
"""
import sys
from easytrader import api

sys.path.append('..')
def get_position():
    client=api.use('ths')
    client.connect('D:/software/ths2/xiadan.exe')
    pos=client.position
    print(pos)

if __name__=='__main__':
    get_position()