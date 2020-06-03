from numbers import Number


def wrap_field(value):
    return f'"{value}"'


def wrap_value(value):
    if isinstance(value, Number):
        return f'{value}'
    else:
        return f'\'{value}\''


def wrap_re(value):
    return f'/{value}/'
