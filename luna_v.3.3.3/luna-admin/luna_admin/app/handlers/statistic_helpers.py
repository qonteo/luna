import re
import socket
import uuid

from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.result import Result


_REQUIRED_PARAMS = []
_DEFAULT_PARAMETERS = {
    'time__lt': 'now()',
    'time__gte': 'now()-1d',
    'group_by': '1h',
    'aggregator': 'count',
}


def isUUID(x):
    try:
        uuid.UUID(x)
        return True
    except ValueError:
        return False


def isIP(x):
    try:
        socket.inet_aton(x)
        return True
    except socket.error:
        return False


_GROUP_BY_RE = re.compile(r'^\d{1,5}(u|ms|s|m|h|d|w)$')
_TIME_RE = re.compile(r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2})|(now\(\)-\d{1,5}(u|ms|s|m|h|d|w))$')
_COMMON_VALIDATE_SCHEMA = {
    'time__lt': lambda x: _TIME_RE.match(x) is not None,
    'time__gte': lambda x: _TIME_RE.match(x) is not None,
    'aggregator': lambda x: x in ('count', 'mean', 'max', 'min'),
    'group_by': lambda x: _GROUP_BY_RE.match(x) is not None,
    'series': lambda x: x in ('extract_success', 'matching_success', 'errors'),
    'account_id': isUUID,
    'server': isIP,

}

_MAIN_VALIDATE_SCHEMA = {
    'extract_success': {
        **_COMMON_VALIDATE_SCHEMA,
        'resource': lambda x: x in ('descriptors',),
        'count_faces': lambda x: x.isdigit(),
    },
    'matching_success': {
        **_COMMON_VALIDATE_SCHEMA,
        'resource': lambda x: x in ('search', 'match', 'identify', 'verify'),
        'limit': lambda x: x.isdigit(),
        'template': lambda x: x in ('0', '1'),
        'candidate': lambda x: x in ('0', '1'),
    },
    'errors': {
        **_COMMON_VALIDATE_SCHEMA,
        'resource': lambda x: x in ('descriptors', 'search', 'match', 'identify', 'verify'),
        'error': lambda x: x.isdigit(),
    }
}

_COMPILE_SCHEMA = {
    'time__lt': lambda x: x if 'now' in x else make_value(x),
    'time__gte': lambda x: x if 'now' in x else make_value(x),

    # both
    'account_id': lambda x: make_value(x),
    'resource': lambda x: make_value(x),
    'server': lambda x: make_value(x),

    # extract
    'count_faces': lambda x: make_value(x),

    # match
    'limit': lambda x: make_value(x),
    'template': lambda x: make_value(x),
    'candidate': lambda x: make_value(x),

    # error
    'error': lambda x: make_value(x),
}


def make_value(value):
    return "'{}'".format(value)


def make_field(field):
    return '"{}"'.format(field)


def check_existence(getter):
    for param in _REQUIRED_PARAMS:
        if getter(param, None) is None:
            return Result(Error.RequiredQueryParameterNotFound,
                          Error.RequiredQueryParameterNotFound.description.format(param))
    return Result(Error.Success, 0)


def validate_params(getter, series):
    params = {'series': series}
    for paramName, param_validator in _MAIN_VALIDATE_SCHEMA[series].items():
        value = getter(paramName, None)
        if value is not None:
            if not param_validator(value):
                msg = Error.BadQueryParams.detail.format(paramName)
                return Result(Error.BadQueryParams, msg)
        elif paramName in _DEFAULT_PARAMETERS:
            value = _DEFAULT_PARAMETERS[paramName]
        else:
            continue
        params[paramName] = value
    return Result(Error.Success, params)


def compile_params(params):
    for name, value in params.items():
        if name in _COMPILE_SCHEMA:
            params[name] = _COMPILE_SCHEMA[name](value)
    where = {k: v for k, v in params.items() if k not in ('aggregator', 'series', 'time__gte', 'time__lt', 'group_by')}
    [params.pop(k) for k in where]
    params['where'] = ''.join(' AND ' + make_field(k) + '=' + v for k, v in where.items())
    return params


def prepare_params(getter, series):
    # check existence
    existenceRes = check_existence(getter)
    if existenceRes.fail:
        return existenceRes
    # check correctness
    paramsRes = validate_params(getter, series)
    if paramsRes.fail:
        return paramsRes
    params = paramsRes.value
    # compile
    compiled_params = compile_params(params)
    return Result(Error.Success, compiled_params)
