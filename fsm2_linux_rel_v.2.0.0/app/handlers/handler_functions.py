from common.helpers import compareGroupByWithTime
from errors.error import Error, Result


def validateParams(getter, schema, required=None):
    """
    Validate query parameters function. Used in events and groups search and stats.

    :param getter: query parameter getter by name
    :param schema: name->(validator, compiler) mapping
    :param required: required query parameter list
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    for name in schema:
        value = getter(name, None)
        if value is None:
            if required is not None and name in required:
                return Result(Error.generateError(
                    Error.QueryParameterNotFound,
                    Error.QueryParameterNotFound.getErrorDescription().format(name)
                ), 0)
            continue
        validator, _ = schema[name]
        if not validator(value):
            return Result(Error.generateError(
                Error.BadQueryParam,
                Error.BadQueryParam.getErrorDescription().format(name)
            ), 0)
    return Result(Error.Success, 0)


def validateStatParams(getter, schema):
    """
    Validate query parameters for statistics request.

    :param getter: query parameter getter by name
    :param schema: name->(validator, compiler) mapping
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    validateRes = validateParams(getter, schema, required=['aggregator', 'group_by'])
    if validateRes.fail:
        return validateRes

    aggregator = getter('aggregator', None)
    if aggregator != 'count':
        if getter('target', None) is None:
            return Result(Error.generateError(Error.QueryParameterNotFound,
                Error.QueryParameterNotFound.getErrorDescription().format('target')), 0)

    group_by = getter('group_by', None)

    time = getter('create_time__gt', None), getter('create_time__lt', None)

    if not compareGroupByWithTime(group_by, time):
        return Result(Error.generateError(
            Error.GroupByTooLow,
            Error.GroupByTooLow.getErrorDescription().format(group_by)
        ), 0)
    return Result(Error.Success, 0)


def compileParams(getter, schema):
    """
    Compile query parameters.

    :param getter: query parameter getter by name
    :param schema: name->(validator, compiler) mapping
    :return: compiled filters
    """
    filters = {}
    for name in schema:
        _, compiler = schema[name]
        value = getter(name, None)
        if value is None:
            continue
        filters[name] = compiler(value)
    return filters


def compressFilters(filters, schema):
    """
    Compress compiled query parameters.

    :param filters: filters to compress
    :param schema: (new_name, (nested1, nested2, ...)) objects tuple
    :return: compressed filters
    """
    for name, nested in schema:
        if any(field in filters for field in nested):
            filters[name] = tuple(filters.pop(field, None) for field in nested)
    return filters
