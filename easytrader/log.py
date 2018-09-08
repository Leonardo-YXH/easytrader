# -*- coding: utf-8 -*-
import logging
from logging import config,handlers
import json
import os

log = logging.getLogger("easytrader")
log.setLevel(logging.DEBUG)
log.propagate = False

fmt = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(filename)s %(lineno)s: %(message)s"
)
ch = logging.StreamHandler()

ch.setFormatter(fmt)
log.handlers.append(ch)

def get_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_trader_log():
    logging.basicConfig()
    log=logging.getLogger('trader')
    log.setLevel(logging.INFO)
    log.propagate=False
    filehandler=logging.handlers.TimedRotatingFileHandler(filename=get_root()+'/logs/trader',when='D',interval=1,backupCount=30,encoding='utf8')
    filehandler.suffix='%Y-%m-%d.log'
    filehandler.setLevel(logging.INFO)
    filehandler.setFormatter(fmt)
    log.addHandler(filehandler)

setup_trader_log()
