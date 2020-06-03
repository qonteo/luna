from src.stat_service.settings.defaults import INFLUX_URL, INFLUX_LOGIN, INFLUX_PASSWORD, INFLUX_DATABASE
from influxdb import InfluxDBClient

client = InfluxDBClient(INFLUX_URL.split(':')[0], int(INFLUX_URL.split(':')[1]), INFLUX_LOGIN, INFLUX_PASSWORD)
client.create_database(INFLUX_DATABASE)
