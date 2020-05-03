# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-04-29
@last modified time:2020-04-29
更新持仓信息
"""
import sys
# sys.path.append('..')

from easytrader import api
from datetime import datetime
from leo.database import account_holding_service_impl
from sqlalchemy import create_engine




def get_position(engine):
    client = api.use('ths')
    client.connect('D:/software/ths2/xiadan.exe')
    pos = client.position
    print(pos)
    now = datetime.now().strftime('%Y-%m-%d')
    data = []
    row_name_to_sql = {'account_no': '股东帐户',
                       'ticker': '证券代码',
                       'name_cn': '证券名称',
                       'qty': '股票余额',
                       'available_qty': '可用余额',
                       'avg_cost': '成本价',
                       'pnl': '盈亏比(%)'
                       }
    for posi in pos:
        row = []
        row.append(posi[row_name_to_sql['account_no']])
        row.append(now)
        row.append(posi[row_name_to_sql['ticker']])
        row.append(posi[row_name_to_sql['name_cn']])
        row.append(posi[row_name_to_sql['qty']])
        row.append(posi[row_name_to_sql['available_qty']])
        row.append(posi[row_name_to_sql['avg_cost']])
        row.append(posi[row_name_to_sql['pnl']])
        data.append(row)
    account_holding_service_impl.restore(engine, data)


if __name__ == '__main__':
    engine = create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/quant_bee?charset=utf8')
    get_position(engine)
