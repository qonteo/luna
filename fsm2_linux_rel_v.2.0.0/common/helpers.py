from uuid import UUID
import re
from datetime import datetime, timedelta
import time


def ifFloat(value):
    """
    Check if value can be represented as float.

    :param value: value to validate
    :return: True or False
    """
    try:
        float(value)
    except ValueError:
        return False
    return True


def ifInt(value):
    """
    Check if value can be represented as integer.

    :param value: value to validate
    :return: True or False
    """
    try:
        int(value)
    except ValueError:
        return False
    return True


def ifUUID(value):
    """
    Check if value can be represented as uuid.

    :param value: value to validate
    :return: True or False
    """
    try:
        UUID(value)
    except ValueError:
        return False
    return True


def ifUUIDs(value):
    """
    Check if value can be represented as coma-separated uuid list.

    :param value: value to validate
    :return: True or False
    """
    try:
        for uuid in value.split(','):
            UUID(uuid)
    except ValueError:
        return False
    return True


def ifTime(value):
    """
    Check if value can be represented as time in rfc3339 with finishing "Z".

    :param value: value to validate
    :return: True or False
    """
    try:
        datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        return False
    return True


def compileTime(value):
    """
    Compile rfc3339 time string into timestamp millis.

    :param value: value to compile
    :return: timestamp
    """
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').timestamp() * 1000


_groupByRe = re.compile(
    r'^((\d{1,5}[smhdwMy])|(monthOfYear)|(dayOfYear)|(dayOfMonth)|(dayOfWeek)|(hourOfDay)|(minuteOfDay))$'
)
_compareGroupByWithTimeRe = re.compile('^\d{1,5}[smhdwMy]$')
_maxTimeDeltaMinGroupBy = (
    ("1h", '5s'),
    ("1d", '1m'),
    ("1M", '10m'),
    ("1y", '1h'),
    ("inf", '1d')
)


def ifGroupBy(value):
    """
    Check if value can be represented as group_by value.

    :param value: value to validate
    :return: True or False
    """
    return isinstance(value, str) and _groupByRe.match(value) is not None


def timedeltaFromParam(value):
    """
    Get time delta from str value with the "<count><time period>" format.

    :param value: value to validate
    :return: datetime.timedelta
    """
    if value[-1] not in 'smhdwMy':
        raise RuntimeError("wrong time dimension")
    if value[-1] in 'smhdw':
        return timedelta(**{
            {
                's': 'seconds',
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
                'w': 'weeks',
            }[value[-1]]: int(value[:-1])
        })
    return timedelta(days=(366 if value[-1] == 'y' else 31) * int(value[:-1]))


def compareGroupByWithTime(group_step, rfc3339Time):
    """
    Compare group by with time period. We deny big data requests.

    :param group_step: str value with the "<count><time period>" format or one of special:
        'monthOfYear', 'dayOfYear', 'dayOfMonth', 'dayOfWeek', 'hourOfDay', 'minuteOfDay'
    :param rfc3339Time: time period tuple
    :return: True if ok, False if not
    """
    if group_step in ('monthOfYear', 'dayOfYear', 'dayOfMonth', 'dayOfWeek', 'hourOfDay', 'minuteOfDay',):
        return True
    if rfc3339Time[0] is None:
        return timedeltaFromParam(_maxTimeDeltaMinGroupBy[-1][1]) <= timedeltaFromParam(group_step)
    if rfc3339Time[1] is None:
        rfc3339Time = rfc3339Time[0], convertTimestampMillisToRfc3339(time.time())
    timeDelta = datetime.strptime(rfc3339Time[1], '%Y-%m-%dT%H:%M:%SZ') - \
                datetime.strptime(rfc3339Time[0], '%Y-%m-%dT%H:%M:%SZ')
    for maxDelta, minGroupBy in _maxTimeDeltaMinGroupBy:
        if maxDelta == 'inf' or timedeltaFromParam(maxDelta) >= timeDelta:
            return timedeltaFromParam(minGroupBy) <= timedeltaFromParam(group_step)


def convertTimestampMillisToRfc3339(timeStamp):
    """
    Convert timestamp to rfc3339.

    :param timeStamp: input timestamp in milliseconds
    :return: '%Y-%m-%dT%H:%M:%SZ'
    """
    if isinstance(timeStamp, float) or isinstance(timeStamp, int):
        return datetime.fromtimestamp(timeStamp//1000).isoformat().split(".")[0] + "Z"
    return timeStamp


def replaceTimeRecursively(mapping, replaceTimeFunc=convertTimestampMillisToRfc3339):
    """
    Recursively replace 'create_time__gt', 'create_time__lt', 'create_time' and 'last_update' values using
    the replaceTimeFunc.

    :param mapping: mapping to search listed fields
    :param replaceTimeFunc: function to apply
    :return: updated mapping
    """
    if isinstance(mapping, dict):
        for k, v in mapping.items():
            if k in ('create_time__gt', 'create_time__lt', 'create_time', 'last_update'):
                mapping[k] = replaceTimeFunc(v)
            if isinstance(v, dict) or isinstance(v, list):
                replaceTimeRecursively(v, replaceTimeFunc)
    elif isinstance(mapping, list):
        for v in mapping:
            replaceTimeRecursively(v, replaceTimeFunc)
    return mapping


def convertRfc3339ToTimestampMillis(rfc3339):
    """
    Convert rfc3339 to timestamp in milliseconds.

    :param rfc3339: '%Y-%m-%dT%H:%M:%SZ'
    :return: timestamp in seconds
    """
    if isinstance(rfc3339, str):
        return round(datetime.strptime(rfc3339, '%Y-%m-%dT%H:%M:%SZ').timestamp()*1000)
    return rfc3339


def getNowTimestampMillis():
    """
    Returns the rounded current timestamp in milliseconds for the compatibility with Elasticsearch.

    :return: current timestamp
    """
    return round(time.time()*1000)


def nestedGetter(dictOrList, path: list):
    """
    Get deep nested object from dict or list hierarchy.

    :param dictOrList: complex list-dict tree
    :param path: key list
    :return: nested object
    """
    try:
        for currentPath in path:
            if isinstance(dictOrList, dict) or isinstance(dictOrList, list):
                dictOrList = dictOrList[currentPath]
            else:
                return None
        else:
            return dictOrList
    except (KeyError, IndexError, TypeError):
        return None

