# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/25'

import pymysql.cursors

from backtesting import settings


def get_mysql_conn():
    return pymysql.connect(**settings.MYSQL_CONF)

