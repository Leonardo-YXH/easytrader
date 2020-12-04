# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-05-20
@last modified time:2020-05-20
"""
from .quant_bee_record import *

def select(session,ticker):
    """

    :param session:
    :param ticker:
    :return:
    """
    return session.query(HuShenHopeDaily).filter(HuShenHopeDaily.code.in_(ticker)).one()

def select(session,tickers):
    """

    :param session:
    :param tickers:
    :return:
    """
    return session.query(HuShenHopeDaily).filter(HuShenHopeDaily.code.in_(tickers)).all()