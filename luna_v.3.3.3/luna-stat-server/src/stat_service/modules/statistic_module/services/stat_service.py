from logging import getLogger
from datetime import timedelta, datetime
import re
from influxdb.exceptions import InfluxDBClientError

from common.api_tools import ApiError
from common.async_influxdb import AsyncInfluxDBClient, InfluxDBServerUnavailableError
from common.flattenizer import lazy_flatten
from common.inflixdb_query_builder import IDBQueryBuilderError

from .filter_models.stat_filter_model import StatQueryBuilder

log = getLogger('ss.stat_module.service.ss')

INFLUX_TIME_INPUT = re.compile(
    '^(?:(\d+[usmhdw])|(now(?:-\d+[usmhdw])?)|(\d{4}(?:-\d{2}(?:-\d{2}(?:-\d{2}(?:-\d{2}(?:-\d{2})?)?)?)?)?))$')


class StatServiceError(ApiError):
    code = 400
    description = 'Malformed query, description: {description}'


class StorageUnavailableError(ApiError):
    code = 500
    description = 'Influx request timeout error'


def to_datetime(req_time):
    """
    Accepts time in INFLUX_TIME_INPUT format
    :param req_time: time to decode
    :return: datetime or timedelta object, may raise ValueError if format is wrong
    """
    if INFLUX_TIME_INPUT.match(req_time) is None:
        raise ValueError
    # the format is 'now-<number><measure>'
    if any(i in req_time for i in 'usmhdw'):
        req_time = req_time.replace('now', '')
        return timedelta(**{
            {
                'u': 'microseconds',
                's': 'seconds',
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
                'w': 'weeks',
                '': 'seconds',
            }[req_time and req_time[-1]]: int(req_time[:-1] or 0)
        })
    else:
        # the format is 'YYYY-MM-DD-hh-mm-ss'

        return datetime.strptime(req_time, {
            0: '%Y',
            1: '%Y-%m',
            2: '%Y-%m-%d',
            3: '%Y-%m-%d-%H',
            4: '%Y-%m-%d-%H-%M',
            5: '%Y-%m-%d-%H-%M-%S',
        }[req_time.count('-')])


def make_delta(end, start):
    if type(end) == type(start):
        return end - start
    if type(end) == timedelta:
        return datetime.now() + end - start
    else:
        return end - datetime.now() - start


def check_group_step(time, group_step):
    """
    Group_step checker referring to time delta
    :param time: list of time__gt and time__lt
    :param group_step: group step to check
    :return: True or False, may raise StatServiceError if wrong time or group_step format
    """
    GROUPSTEP_BY_DURATION = {
        '1h': '5s',
        '1d': '1m',
        '4w': '10m'
    }
    if time[0] is None:
        time[0] = 'now-3h'
    if time[1] is None:
        time[1] = 'now'
    try:
        start = to_datetime(time[0])
    except (ValueError, OverflowError):
        raise StatServiceError(description=f'time__gt parameter has wrong value "{time[0]}"')
    try:
        end = to_datetime(time[1])
    except (ValueError, OverflowError):
        raise StatServiceError(description=f'time__lt parameter has wrong value "{time[1]}"')
    delta = make_delta(end, start)
    try:
        for k in sorted(GROUPSTEP_BY_DURATION, key=to_datetime):
            if abs(delta) <= to_datetime(k):
                break
        else:
            return abs(to_datetime(group_step)) >= to_datetime('1h')
        return abs(to_datetime(group_step)) >= to_datetime(GROUPSTEP_BY_DURATION[k])
    except (ValueError, OverflowError):
        raise StatServiceError(description=f'group_step parameter has wrong value "{group_step}"')


def update_absolute_time_filters(filters):
    for name in ('time__gt', 'time__lt'):
        if filters.get(name, None) is None or any(i in filters.get(name) for i in 'usmhdw'):
            continue
        try:
            filters[name] = str(int(to_datetime(filters[name]).timestamp()*10**9))
        except ValueError:
            raise IDBQueryBuilderError(f'"{name}" parameter has bad value "{filters[name]}"')


class StatService(object):
    """
    Perform accessing to events data from InfluxDB storage
    """

    def __init__(self, influx_client: AsyncInfluxDBClient):
        self.influx_client = influx_client

    async def query(self, account_id, fields=None, group_step=None, aggregator='max', **filters):
        """
        Build InfluxDB query from given parameters, query DB and return data.

        :param account_id: user account id
        :param fields: names of fields, which will be queried
        :param group_step: group result using step
        :param aggregator: collapse group using comparator
        :param filters: filter values using this values. Refer to `StatQueryBuilder` for full explanation.
        """
        if not check_group_step([filters.get(item) for item in ('time__gt', 'time__lt')], group_step=group_step):
            raise StatServiceError(description='group_step is too small')
        update_absolute_time_filters(filters)

        try:
            builder = StatQueryBuilder(
                select_field_operator='{}({})'.format(aggregator, '{}')
            )

            builder.apply_filters(
                dict(
                    account_id=account_id,
                    **(filters or {})
                )
            )

            if fields is not None:
                builder.set_fields(fields)

            if group_step is not None:
                builder.set_group_step(group_step)

            query = builder.build()
            log.debug(f'Performing query "{query}"')

            try:
                res = await self.influx_client.request(
                    'query', 'GET', {'q': query}
                )
            except InfluxDBServerUnavailableError:
                log.exception('Influx server unavailable, original error', exc_info=True)
                raise StorageUnavailableError()
            except InfluxDBClientError as e:
                log.exception('Influx server got exception', exc_info=True)
                raise StatServiceError(code=e.code, description=e.content)

            res = lazy_flatten(res)['results.0.series.0']
            if res is not None and 'columns' in res:
                if 'name' in res:
                    del res['name']
                if fields is None:
                    fields = [c[len(aggregator) + 1:] for c in res['columns'][1:]]
                res['columns'] = ['time'] + fields

            return res or {}
        except IDBQueryBuilderError as err:
            raise StatServiceError(description=str(err))

    @classmethod
    def get_allowed_filters(cls):
        return StatQueryBuilder.FilterModel.get_all_filter_names()
