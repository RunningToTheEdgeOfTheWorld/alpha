import os
import re
from datetime import datetime
from strategy import logger, sql, db_write_access, tables

raw_dir = './candles_1m'
sql_create = """CREATE TABLE {table} 
                (pid integer primary key autoincrement, exchange text, symbol text, timestamp_ms double not null, 
                 o_price double not null, h_price double not null, l_price double not null, 
                 c_price double not null, volume double not null)"""
sql_insert = """INSERT INTO {table}(exchange, symbol, timestamp_ms, o_price, h_price, l_price, c_price, volume) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
r = re.compile('qdc_db\.([a-z]*)_([_A-Z]*)_candle_1m.*, ([\d.]*), ([\d.]*), ([\d.]*), ([\d.]*), ([\d.]*), ([\d.]*)\)$')


def main():
    with db_write_access():
        for i in os.listdir(raw_dir):
            if i.endswith('_candle_1m.sql'):
                t = datetime.now()
                with open(os.path.join(raw_dir, i), 'r') as f:
                    records = f.read().split(';')
                logger.info('{}: inserting {} records'.format(i, len(records) - 1))
                for record in records:
                    matched = r.search(record)
                    if matched:
                        exchange, symbol, timestamp_ms, o_price, h_price, l_price, c_price, volume = matched.groups()
                        table = 'quotes_' + datetime.fromtimestamp(int(timestamp_ms) / 1e3).strftime('%Y%m%d')
                        if table not in tables:
                            sql.execute(sql_create.format(table=table))
                            tables.add(table)
                        sql.execute(sql_insert.format(table=table), matched.groups())
                logger.debug('{}: time elapsed {}'.format(i, datetime.now() - t))


if __name__ == '__main__':
    main()
