# -*- coding:utf-8 -*-
"""
@author: leonardo
@created time: 2020-05-20
@last modified time:2020-05-20
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Index, DATETIME, FLOAT, DATE
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, or_, and_

Base = declarative_base()


class HuShenHopeDaily(Base):
    __tablename__ = 'hushen_hope_daily'
    id = Column(Integer, primary_key=True)
    code = Column(String)
    base_price = Column(FLOAT)
    delta = Column(FLOAT)
    today_open = Column(FLOAT)
    today_close = Column(FLOAT)
    today_high = Column(FLOAT)
    today_low = Column(FLOAT)
    tomorrow_open = Column(FLOAT)
    tomorrow_close = Column(FLOAT)
    tomorrow_high = Column(FLOAT)
    tomorrow_low = Column(FLOAT)
    buy_flag = Column(FLOAT)


class AccountHolding(Base):
    """
    账户每日持仓
    """
    __tablename__ = 'account_holding'
    account_no = Column(String, primary_key=True)
    time_x = Column(DATE, primary_key=True)
    ticker = Column(String, primary_key=True)
    name_cn = Column(String)
    qty = Column(FLOAT)
    available_qty = Column(FLOAT)
    avg_cost = Column(FLOAT)
    pnl = Column(FLOAT)
