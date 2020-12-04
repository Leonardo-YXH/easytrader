# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-11-03
@last modified time:2020-11-03
"""
from sqlalchemy import create_engine,event
import numpy as np

def get_connection(database_name):
    """

    :param database_name:
    :return:
    """
    return create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/{}?charset=utf8'.format(database_name))

def add_own_encoders(conn, cursor, query, *args):
    cursor.connection.encoders[np.float64] = lambda value, encoders: float(value)
    cursor.connection.encoders[np.int32] = lambda value, encoders: int(value)



def enable_np_encoder(engine):
    """
    py_mysql支持np.float64 translate
    :param engine:
    :return:
    """
    event.listen(engine, "before_cursor_execute", add_own_encoders)