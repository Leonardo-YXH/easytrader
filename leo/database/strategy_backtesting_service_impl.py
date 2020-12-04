# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-11-03
@last modified time:2020-11-03
"""


def select(engine, backtesting_id):
    """

    :param engine:
    :param backtesting_id:
    :return:
    """
    sql = 'SELECT * from strategy_backtesting where backtesting_id="{}"'.format(backtesting_id)
    return list(engine.execute(sql))


def insert_on_duplicate_update(engine, data):
    """

    :param engine:
    :param data:
    :return:
    """
    sql = 'insert into strategy_backtesting(backtesting_id,strategy_id ,strategy_param,backtesting_start_time,backtesting_end_time)' \
          ' values (%s,%s,%s,%s,%s)' \
          ' on duplicate key update backtesting_id=values(backtesting_id),strategy_id=values(strategy_id),strategy_param=values(strategy_param),backtesting_start_time=values(backtesting_start_time),backtesting_end_time=values(backtesting_end_time)'
    return engine.execute(sql, data)
