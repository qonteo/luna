import string


_formatter = string.Formatter()


class _MissingKeyAsValue(dict):
    def __missing__(self, key):
        return '{' + key + '}'


class _MissingKeyAsEmptyStr(dict):
    def __missing__(self, key):
        return ''


def partially_format(s, *args, strategy=None, **kwargs):
    return _formatter.vformat(
        s, args, _MissingKeyAsValue(kwargs) if strategy is not None else _MissingKeyAsEmptyStr(kwargs)
    )
