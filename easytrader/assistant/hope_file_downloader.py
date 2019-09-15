# -*-coding:utf-8-*-

import os
import time
from datetime import date
from ftplib import FTP
import pandas as pd

# 服务器地址
FTP_SERVER = '106.14.153.239'
USER = 'yxh'
PWD = 'yangxh'
FTP_PATH = '/'
local_root = 'E:\\projects\\python\\beestock\\data\\result'
DATE = time.strftime('%Y%m%d', time.localtime(time.time()))


def isDir(filename):
    try:
        path = filename;
        path.replace('/', '\\')
        if os.path.exists(path):
            print('---file exists--')
        else:
            print('file not exists ', local_root)
            os.mkdirs(local_root)
        return True
    except:
        return False


def ftpconnect():
    ftp = FTP()
    ftp.set_debuglevel(2)
    ftp.connect(FTP_SERVER, 21)
    ftp.login(USER, PWD)
    return ftp


def downloadfile():
    ftp = ftpconnect()
    ftp.cwd(FTP_PATH)
    ftp.set_pasv(0)
    li = ftp.nlst()
    print('ftp: ', li)
    i = 0
    for eachfile in li:
        i += 1
        if i > 1:
            break
        localpath = 'e:' + eachfile
        print('-- open localpath --', localpath)
        bufsize = 1024
        isDir(localpath)
        fp = open(localpath, 'wb+')
        code = ftp.retrbinary('RETR ' + eachfile, fp.write, bufsize)
        print('+++++++++++++:', code)
        fp.flush()

    ftp.set_debuglevel(0)  # 关闭调试
    # fp.close()
    ftp.quit()  # 退出ftp服务器


def synchronize_result_file():
    """

    :return:
    """
    today = date.today()

    if today.isoweekday() > 5:  # 周六周日不执行
        return

    ftp = ftpconnect()
    ftp.cwd(FTP_PATH)
    ftp.set_pasv(0)
    date_str = date.today().strftime('%Y-%m-%d')

    hope_file = 'hope_stock_' + date_str + '.csv'
    update_result_file(hope_file, local_root, ftp, 'Y_ZIXUAN.blk')

    hope_file = 'hope_stock_' + date_str + '_limitup.csv'
    update_result_file(hope_file, local_root, ftp, 'Y_UP.blk')


def update_result_file(filename, local_path, ftp, tdx_group):
    """

    :param filename:
    :param local_path:
    :param ftp:
    :param tdx_group:
    :return:
    """
    abs_file = local_path + '/' + filename
    if os.path.exists(abs_file):
        print(abs_file + '    exists!')
        df = pd.read_csv(abs_file, encoding='utf8', dtype={'code': str})
        update_tdx_group(df, tdx_group, 600)
        print(abs_file + '    update tdx successfully!')
        return
    else:
        fp = open(abs_file, 'wb')
        try:
            code = ftp.retrbinary('RETR ' + filename, fp.write, 1024)
            fp.flush()
        except Exception:
            fp.close()
            os.remove(abs_file)
        else:
            if code.startswith('226'):  # 同步成功，更新通达信自选股
                df = pd.read_csv(abs_file, encoding='utf8', dtype={'code': str})
                update_tdx_group(df, tdx_group, 600)
            fp.close()


def update_tdx_group(data, tdx_group, size):
    """
    更新通达信的自定义品种
    :param data:
    :param tdx_group:
    :param size:
    :return:
    """
    tdx_path = 'D:\\Program Files\\new_txd\T0002\\blocknew\\'
    f = open(tdx_path + tdx_group, 'w')
    i = 0
    for _, item in data.iterrows():
        if item['code'].startswith('60'):
            f.write('1' + item['code'])
            f.write('\n')
        else:
            f.write('0' + item['code'])
            f.write('\n')
        i += 1
        if i >= size:
            break
    f.flush()
    f.close()


if __name__ == "__main__":
    # downloadfile()
    # f=open(local_root+'/hope_stock_2018-09-21_limitup.csv','r')
    # data=pd.read_csv(f,encoding='utf8',dtype={'code':str})
    # update_tdx_group(data,'Y_UP.blk',600)
    synchronize_result_file()
