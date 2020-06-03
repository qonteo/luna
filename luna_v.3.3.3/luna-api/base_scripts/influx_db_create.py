from set_working_directory import setWorkingDirectory

setWorkingDirectory()

from influxdb import InfluxDBClient

from configs.config import ADMIN_STATISTICS_DB, ADMIN_STATISTICS_SERVER_ORIGIN


def getPort():
    return ADMIN_STATISTICS_SERVER_ORIGIN.split(':')[-1]


def getHost():
    host = ADMIN_STATISTICS_SERVER_ORIGIN.split(':')[1]
    return host[2:]


client = InfluxDBClient(getHost(), getPort(), 'root', 'root')
client.create_database(ADMIN_STATISTICS_DB)
