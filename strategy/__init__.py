import logging
import sqlite3
import pandas
from datetime import datetime
from contextlib import contextmanager

pandas.options.display.width = 200


def get_logger():
    log = logging.getLogger('fintend-strategy')
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter('%(asctime)s %(levelname)s: [%(processName)s(%(process)s)/%(threadName)s(%(thread)s)/'
                            '%(name)s.%(module)s::%(funcName)s] %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)
    return log


logger = get_logger()
db_path = '/Users/sweetdreams/code/fintend/alpha/db/fintend.sqlite3'
conn = sqlite3.connect(db_path)
sql = conn.cursor()
tables = set(i[0] for i in sql.execute('SELECT name FROM sqlite_master WHERE type="table"'))


@contextmanager
def db_write_access():
    yield
    t = datetime.now()
    logger.debug('commit ...')
    conn.commit()
    logger.info('commit time elapsed {}'.format(datetime.now() - t))
