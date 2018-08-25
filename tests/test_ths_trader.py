# -*- coding: utf-8 -*-
from easytrader import api

if __name__=='__main__':
    client=api.use('ths',debug=False)
    client.connect(r"D:\\software\\ths\\xiadan.exe",timeout=5)
    # client.connect(r"D:\\Eastmoney\\Choice\\bin\\EmStart.exe",timeout=5)

    help_msg="""1--buyF1
    2--sellF2
    3--chedanF3
    4--searchF4:chicang
    5--F4:today:trader
    6--F4:today:entrusts
    """
    print(help_msg)
    msg=input("please input your choice:")
    while True:
        if msg=='1':
            client.buy('603776',25.122,100)
        elif msg=='2':
            client.sell('603776',25.13,amount=100)
        elif msg=='3':
            client.cancel_entrust(input('order no:'))
        elif msg=='3.1':
            print(client.cancel_entrusts)
        elif msg=='3.2':
            print(client.cancel_all_entrust())
        elif msg=='3.3':
            print(client.cancel_all_sell_entrust())
        elif msg=='3.4':
            print(client.cancel_all_buy_entrust())
        elif msg == '4':
            print(client.balance)
        elif msg == '4.1':
            print(client.position)
        elif msg=='5':
            print(client.today_trades)
        elif msg=='6':
            print(client.today_entrusts)
        else:
            break
        print(help_msg)
        msg = input("please input your choice:")