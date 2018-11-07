# !/usr/bin/env python
__author__ = 'Rick Zhang'
__time__ = '2018/8/25'


import os
import sys
import logging

from backtesting import settings
from backtesting.json_logger import get_json_logger, JsonFormatter

BACKTESTING_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_logger(name='root'):
    class LevelFilter(object):
        def __init__(self, level):
            self.__level = level

        def filter(self, log_record):
            return log_record.levelno <= self.__level

    logger = get_json_logger(name)
    logger.propagate = False
    if not logger.handlers:
        formatter = JsonFormatter(
            {
                'logger': name,
                'asctime': '%(asctime)s',
                'level': '%(levelname)s',
                'message': '%(message)s',
            }
        )

        sh_i = logging.StreamHandler(sys.stdout)
        sh_i.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        sh_i.setFormatter(formatter)
        sh_i.addFilter(LevelFilter(logging.INFO))

        sh_e = logging.StreamHandler(sys.stderr)
        sh_e.setFormatter(formatter)
        sh_e.setLevel(logging.ERROR)

        logger.addHandler(sh_i)
        logger.addHandler(sh_e)
    return logger
