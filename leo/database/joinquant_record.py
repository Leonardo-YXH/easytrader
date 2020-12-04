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


class OrderRecord(Base):
    __tablename__ = 'order_record'
    strategy_id = Column(Integer, primary_key=True)
    execute_time = Column(DATETIME,primary_key=True)
    ticker = Column(String,primary_key=True)
    order_side = Column(Integer,primary_key=True)
    amount=Column(Integer)
    order_type = Column(Integer)
    price = Column(FLOAT)
    create_time = Column(DATETIME)
    status = Column(Integer)

    def __repr__(self):
        tpl='strategyId={},ticker={},amount={},orderSide={},orderType={},executeTime={}'
        return tpl.format(self.strategy_id,self.ticker,self.amount,self.order_side,self.order_type,self.execute_time)

if __name__ == '__main__':
    engine=create_engine('mysql+pymysql://root:yangxh@106.14.153.239:3306/join_quant_backtesting?charset=utf8')
    session=sessionmaker(bind=engine)()
    rs=session.query(OrderRecord).filter(and_(OrderRecord.strategy_id.in_([1]),
                                           OrderRecord.execute_time>'2020-11-00 00:00:00')).all()
    print(rs)


