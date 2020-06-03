import re
from abc import abstractmethod
from enum import Enum
from itertools import chain
from datetime import datetime

import pytz
from dateutil.parser import parse

from common.meta_utils import CollectFieldsIntoClassAttribute

from .exceptions import IDBQueryBuilderError, IDBQueryBuilderNotImplementedError
from .utils import wrap_field, wrap_value, wrap_re


class InfluxDBTypesChecker(object):
    """
    Wrap and process the most common InfluxDB types
    """
    _INFLUX_DB_TIME_INTERVAL_REG_EXPR = re.compile(
        r'^-?\d+[usmhdw]$'
    )
    _INFLUX_DB_TIME_REG_EXPR = re.compile(
        r'^(now(\s?-\s?\d+[usmhdw])?)|(\d{19,21})$'
    )

    @classmethod
    def create_time_interval(cls, value):
        if cls._INFLUX_DB_TIME_INTERVAL_REG_EXPR.match(
                value
        ) is None:
            raise ValueError(
                f'Unexpected time interval given "{value}"'
            )
        return value

    @classmethod
    def create_timestamp(cls, value):

        match = cls._INFLUX_DB_TIME_REG_EXPR.match(
            value
        )
        if match is None:
            raise ValueError(f'Wrong timestamp "{value}"')

        is_now, time_shift, date = match.groups()
        if time_shift is not None:
            time_shift = time_shift.replace(' ', '').replace('-', '- ')
        elif date is not None:
            time_shift = value
        else:
            time_shift = ''
        return f"{('now() ' if is_now else '')}{time_shift}"

    @classmethod
    def create_event_type(cls, value):
        if value not in ('match', 'extract', 'identify'):
            raise ValueError(f'Unexpected event type requested "{value}"')
        return wrap_value(value)

    @classmethod
    def create_str(cls, value):
        return wrap_value(value)

    @classmethod
    def create_re(cls, value):
        return wrap_re('('+'|'.join(value.split(','))+')')

    @classmethod
    def create_float(cls, value):
        return wrap_value(float(value))


class FilterCondition(Enum):
    """
    Enumerated structure for replacing Django-style operators with InfluxDB-style
    """
    eq = '='
    lt = '<'
    le = '<='
    gt = '>'
    ge = '>='
    ne = '!='
    mp = '=~'

    @classmethod
    def ensure_enum(cls, value):
        """
        The function ensure that the value is a cls instance
        :param value: value to make an instance
        :return:
        """
        return value if isinstance(value, cls) else cls[value]


class BaseFilterConditionBuilder(object):
    """
    Build filter condition statement like `time > now() - 3h AND tag_1 = 100` from the given filter set
    """

    FILTER_NAME_REG_EXPR = re.compile(
        r'^(\w*?)(?:__({}))?$'.format(
            '|'.join(
                [c.name for c in FilterCondition]
            )
        )
    )

    def __init__(
        self, type_validator, allowed_conditions, restrictions=None, default_condition=None, required=False
    ):
        """
        Init builder.
        :param type_validator: used to validate and wrap filter value
        :param allowed_conditions: tuple, which describes allowed conditions for the given tag
        :param restrictions:
        :param default_condition: tuple, which contains default condition and value
        :param required: whther the field is required or not
        """
        self.type_validator = type_validator
        self.allowed_conditions = [
            FilterCondition.ensure_enum(c)
            for c in allowed_conditions
        ]
        self.restrictions = restrictions

        if default_condition is not None:
            condition, value = default_condition
            self.default_condition = (
                FilterCondition.ensure_enum(condition), value
            )
        else:
            self.default_condition = None

        self.required = required
        self.tag_name = None

    @classmethod
    def parse_filter_name(cls, filter_name):
        """
        Parse filter name in "Django ORM like" form into tuple, which contains tag name and filter condition.
        """

        match = cls.FILTER_NAME_REG_EXPR.match(filter_name)
        if match is None:
            raise IDBQueryBuilderError(
                f'Malformed filter query "{filter_name}"'
            )
        tag_name, condition = match.groups()

        return tag_name, FilterCondition[condition] if condition is not None else condition

    def set_tag_name(self, tag_name):
        self.tag_name = tag_name

    def check_restrictions(self, context):
        if self.restrictions is not None:
            for watched_field, restriction_evaluator in self.restrictions.items():
                if (
                    watched_field in context and
                    not restriction_evaluator(context[watched_field])
                ):
                    raise IDBQueryBuilderError(
                        f'Given filter for tag "{self.tag_name}" has been '
                        f'rejected by "{watched_field}" tag with value "{context[watched_field]}"'
                    )

    def build(self, condition, value):
        if condition is None and value is None:
            condition, value = self.default_condition
        elif condition is None:
            condition = FilterCondition.eq

        if condition not in self.allowed_conditions:
            raise IDBQueryBuilderError(
                f'Unexpected condition given "{condition}" for tag "{self.tag_name}"'
            )

        try:
            value = self.type_validator(value)
        except ValueError as err:
            raise IDBQueryBuilderError(
                f'Type validator on tag value "{self.tag_name}" raise: {str(err)}'
            )

        return f'{wrap_field(self.tag_name)} {condition.value} {value}'


class ThresholdFilterConditionBuilder(BaseFilterConditionBuilder):
    """
    Build filter condition statement, which acts like `tag = 'value'`, but in fact it compares value with threshold, and, depending on initial value, `real_variable` is less or greater then the threshold
    """
    def __init__(self, side_values, threshold, **kwargs):
        """
        Init builder
        :param side_values:
        :param threshold:
        """
        self.threshold = threshold
        self.side_values = side_values
        super().__init__(lambda x: x, ('ge', 'lt'), **kwargs)

    def build(self, condition, value):
        side = self.side_values.index(value)
        if side == -1:
            raise IDBQueryBuilderError(
                f'Expected value one of the [{", ".join(self.side_values)}], got "{value}"'
            )

        if side == 0:
            condition = FilterCondition.lt
        elif side == 1:
            condition = FilterCondition.ge

        return super().build(condition, self.threshold)


class AbstractWhereStatementBuilder(object):
    """
    Build WHERE statement from the given filters, validate and join them using AND keyword
    """
    _all_filter_names = None

    @classmethod
    @abstractmethod
    def get_filter_builders(cls):
        pass

    @classmethod
    @abstractmethod
    def get_required_fields(cls):
        pass

    @classmethod
    @abstractmethod
    def get_default_builders(cls):
        pass

    @classmethod
    def get_all_filter_names(cls):
        return cls._all_filter_names

    @classmethod
    def _get_all_filter_names(cls):
        """
        Get all possible filter names
        :return: list
        """
        return list(
            chain.from_iterable(
                chain(
                    (
                        '{}__{}'.format(tag, c.name)
                        for c in builder.allowed_conditions
                        if c != FilterCondition.eq
                    ),
                    [tag] if FilterCondition.eq in builder.allowed_conditions else []
                )
                for tag, builder in cls.get_filter_builders().items()
            )
        )

    def __init__(self):
        self._filter_descriptors = None
        self._processed_filters = None
        self._default_builders = self.get_default_builders().copy()
        self._required_filters = self.get_required_fields().copy()

    def _add_filters(self, iterable):
        # make it full lazy
        if self._processed_filters is not None:
            self._processed_filters = chain(
                iterable,
                self._processed_filters
            )
        else:
            self._processed_filters = iterable

    def _apply_filter(self, context, name, value):
        tag_name, condition = BaseFilterConditionBuilder.parse_filter_name(
            name
        )

        if tag_name not in self.get_filter_builders():
            raise IDBQueryBuilderError(
                f'Unexpected tag name "{tag_name}"'
            )

        for c in (self._default_builders, self._required_filters):
            try:
                c.remove(tag_name)
            except ValueError:
                pass

        builder = self.get_filter_builders()[tag_name]
        builder.check_restrictions(context)
        return builder.build(condition, value)

    def apply_filters(self, filter_descriptors):
        self._add_filters(
            self._apply_filter(filter_descriptors, field_name, value)
            for field_name, value in filter_descriptors.items()
        )
        return self

    def build(self):
        statements = list(
            chain(
                self._processed_filters,
                (
                    self.get_filter_builders()[f].build(None, None)
                    for f in self._default_builders
                )
            )
        )

        if len(self._required_filters) > 0:
            raise IDBQueryBuilderError(
                'There are some tags required: {}'.format(
                    ', '.join(['"{}"'.format(tag) for tag in self._required_filters])
                )
            )

        return ' AND '.join(statements)


class AbstractInfluxDBQueryBuilder(object):
    """
    High-level class, which is developed to build InfluxDB query from the specified parameters.
    """

    where_builder_cls = AbstractWhereStatementBuilder

    def __init__(self, select_field_operator='max({})', series_name=None):
        self._where_builder = self.where_builder_cls()
        self._filters = None
        self._select_field_operator = select_field_operator
        self._fields = select_field_operator.format('*')
        self._group_by = 'time(1h)'
        self._series_name = series_name

    def set_series_name(self, series_name):
        self._series_name = series_name

    def set_fields(self, desired_fields):
        self._fields = ', '.join(
            self._select_field_operator.format(wrap_field(f))
            for f in desired_fields if self._test_field(f)
        )

        return self

    def apply_filters(self, filters):
        self._where_builder.apply_filters(filters)
        self._filters = filters
        return self

    def _test_field(self, field):
        """
        Test field is allowed.
        Reimplement this method in subclasses if you want unusual behavior, for example, to set fields dependancy on some filter values.
        :param field:
        :return: True is allowed
        """
        return True

    def _get_series_name(self):
        """
        Return series name, specified in the constructor. The query is performed on this name.
        Reimplement it in subclasses, if series name depends on different external conditions.
        There is the guaranty that this method is called all filter fields are validated.
        :return: series name
        """
        return self._series_name

    def set_group_step(self, time):
        InfluxDBTypesChecker.create_time_interval(time)
        self._group_by = f'time({time})'
        return self

    def build(self):
        where = 'WHERE {}'.format(self._where_builder.build()) if self._filters is not None else ''
        series_name = self._get_series_name() or '*'
        return f'' \
               f'SELECT {self._fields} ' \
               f'FROM "{series_name}" ' \
               f'{where} ' \
               f'GROUP BY {self._group_by} fill(none)'


"""""""""""""""""""""""""""
META Driven implementations
"""""""""""""""""""""""""""


class WhereStatementBuilderMeta(CollectFieldsIntoClassAttribute):
    """
    Collect builder, which is declared as class fields
    """
    def __new__(mcs, name, bases, fields):
        fields['_defaults'] = None
        fields['_required'] = None
        cls = super().__new__(
            mcs, name, bases, fields, '_filters',
            allow_instances=BaseFilterConditionBuilder,
            name_field_func=BaseFilterConditionBuilder.set_tag_name
        )
        cls._defaults = [
            k for k, v in cls._filters.items() if v.default_condition is not None
        ]
        cls._required = [
            k for k, v in cls._filters.items() if v.required
        ]
        cls._all_filter_names = cls._get_all_filter_names()

        return cls


class WhereStatementBuilder(
    AbstractWhereStatementBuilder,
    metaclass=WhereStatementBuilderMeta
):
    """
    Implement abstract methods, which return data collected by metaclass
    """
    # just superposes annoying IDE inspection warnings, defined in WhereStatementBuilderMeta
    _defaults = None
    _filters = None
    _required = None

    @classmethod
    def get_default_builders(cls):
        return cls._defaults

    @classmethod
    def get_required_fields(cls):
        return cls._required

    @classmethod
    def get_filter_builders(cls):
        return cls._filters


class InfluxDBQueryBuilderMeta(type):
    """
    Find the nested class with name `FilterModel` and take filter declarations from it.
    """

    filter_model_cls_name = 'FilterModel'

    def __new__(mcs, name, bases, fields):
        if InfluxDBQueryBuilderMeta.filter_model_cls_name in fields:
            filter_model = fields[InfluxDBQueryBuilderMeta.filter_model_cls_name]
            if not isinstance(filter_model, AbstractWhereStatementBuilder):
                class FilterModel(filter_model, WhereStatementBuilder):
                    pass

                filter_model = FilterModel
                fields[InfluxDBQueryBuilderMeta.filter_model_cls_name] = FilterModel
            fields['where_builder_cls'] = filter_model

        cls = super().__new__(mcs, name, bases, fields)
        return cls


class InfluxDBQueryBuilder(AbstractInfluxDBQueryBuilder, metaclass=InfluxDBQueryBuilderMeta):
    """
    Construct `AbstractInfluxDBQueryBuilder.where_builder_cls` from declaration of the nested class `FilterModel`
    """
    pass
