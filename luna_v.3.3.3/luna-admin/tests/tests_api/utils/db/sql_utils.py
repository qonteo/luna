import psycopg2
import cx_Oracle
from utils.common.config_loader import ConfigLoader


class SqlUtils:
    def __init__(self, conn_url=ConfigLoader.get_db_url()):
        if conn_url['dbType'] == 'postgres':
            url = "dbname='{}' user='{}' host='{}' password='{}' port='{}'".format(conn_url['dbName'],
                                                                                   conn_url['dbUser'],
                                                                                   conn_url['dbHost'],
                                                                                   conn_url['dbPass'],
                                                                                   conn_url['dbPort'])
            self.dbContextManager = psycopg2.connect(url)
        elif conn_url['dbType'] == 'oracle':
            url = '{}/{}@{}:{}/{}'.format(conn_url['dbUser'], conn_url['dbPass'], conn_url['dbHost'],
                                          conn_url['dbPort'], conn_url['dbName'])
            self.dbContextManager = cx_Oracle.connect(url)

    def execute_select(self, sql):
        with self.dbContextManager as conn:
            cursor = conn.cursor()
            cursor.execute(sql)

    def execute_update(self, sql):
        with self.dbContextManager as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
