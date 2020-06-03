from collections import Mapping, Callable
from contextlib import contextmanager
from functools import partial
from itertools import chain
from types import FunctionType

from fastcache._lrucache import clru_cache

from common.api_tools.api_tools import BadRequest

class KeyMapError(ValueError):
    """
    Exception to raise when needed key not presented
    """
    pass


class FlattenizerListExpectedError(Exception):
    """
    Exception to raise when did not get list when needed
    """
    pass


class FlattenizerDictExpectedError(Exception):
    """
    Exception to raise if did not get dict when needed
    """
    pass


def lazy_flatten(dictionary, silent_key_error=True, silent_index_error=False):
    """
    Wrapper for _LasyFlattenizer with silent_key_error=True and silent_index_error=False
    :param dictionary:
    :param silent_key_error:
    :param silent_index_error:
    :return:

    Example usage:
    >>>d = {
    ...  'val': {
    ...    'child': [
    ...        {
    ...            'param': 10,
    ...            'nested_list': [
    ...                {
    ...                    'nested_param': {
    ...                        'param': 10
    ...                    }
    ...                },
    ...                {
    ...                    'nested_param': {
    ...                        'param': 100
    ...                    }
    ...                }
    ...            ]
    ...        },
    ...        {
    ...            'param': 100,
    ...            'nested_list': [
    ...                {
    ...                    'nested_param': {
    ...                        'param': 'value'
    ...                    }
    ...                }
    ...            ]
    ...        },
    ...        {
    ...            'param': 1000
    ...        }
    ...    ]
    ...  }
    ...}
    ...
    ...assert lazy_flatten(d)['val.child.*.param'] == [10, 100, 1000]
    ...assert lazy_flatten(d)['val.child.1.param'] == [100]
    ...assert lazy_flatten(d)['val.child.0.param'] == [10]
    ...assert lazy_flatten(d)['val.child.*.nested_list.*.nested_param'] == [
    ...   [
    ...       10, 100
    ...   ],
    ...   [
    ...       'value'
    ...   ]
    ...]
    """
    return _LazyFlattenizer(dictionary, silent_key_error, silent_index_error)


class FlattenizerField(object):
    def __init__(
            self, path, second=None, nested=None, aggregator=None, default=None
    ):
        assert nested is None or aggregator is None, 'Only one value allowed'
        if aggregator is None and nested is None and second is not None:
            if isinstance(second, type):
                if issubclass(second, FlattenizerModel):
                    nested = second
            elif isinstance(second, Callable):
                aggregator = second
            else:
                default = second

        self.flattenizer = compiled_flattenizer(path)
        self.aggregator = aggregator
        self.default = default
        self.nested = nested

    def __call__(self, source):
        val = self.flattenizer(source)
        if val is None:
            val = self.default
        elif self.aggregator is not None:
            val = self.aggregator(val)
        elif self.nested is not None:
            val = [
                i for i in (
                    self.nested(item)
                    for item in val
                ) if i is not None
            ]
        return val


class FlattenizerMapper(object):
    """
    Usage example:
    >>> mapping = {
    ...     'extracted_value_1': 'vals.0.nested',
    ...     'extracted_values': 'vals.*.nested',
    ...     'summed': (sum, 'vals.*.nested'),
    ...     'count': (len, 'vals.*')
    ... }
    ... source = {'vals': [{'nested': 1}, {'nested': 1}, {'nested': 1}, {'nested': 1}, {'noise': 1}]}
    ... extractor = FlattenizerMapper(mapping)
    ... assert extractor['extracted_value_1'](source) == 1
    ... assert extractor['extracted_values'](source) == [1, 1, 1, 1]
    ... assert extractor['summed'](source) == 4
    ... assert extractor['count'](source) == 5
    ... with extractor.for_source(source) as extractor:
    ...     assert extractor['extracted_value_1'] == 1
    ...     assert extractor['extracted_values'] == [1, 1, 1, 1]
    ...     assert extractor['summed'] == 4
    ...     assert extractor['count'] == 5
    """

    def __init__(self, mapping):
        self._extractors = {}
        self._init_extractors(mapping)
        self._source = None

    @staticmethod
    def _extract(aggregator, mapper, source, default=None):
        """
        Extract the resource by mapper from the source then check if operation was correct via aggregator or via default if None
        :param aggregator: function to check correctness
        :param mapper: function to extract from source
        :param source: source (e.g. query parameters dict)
        :param default: default value if not extracted
        :return: value or raise
        """
        res = mapper(source)
        if res is None:
            return default
        return aggregator(res)

    def _init_extractors(self, mapping):
        """
        Prepare and write extractors in self._extractors
        :param mapping: mapping to make extractors on
        :return:
        """
        if isinstance(mapping, Mapping):
            items = mapping.items()
        else:
            items = mapping

        for map_to, map_from in items:
            aggregator = None
            if isinstance(map_from, tuple):
                if len(map_from) == 2:
                    aggregator, map_from = map_from
                    default = None
                elif len(map_from) == 3:
                    aggregator, map_from, default = map_from
                else:
                    raise ValueError(f'Unexpected mapping value {map_from}')

                flattenizer = compiled_flattenizer(map_from)
                extractor = partial(self._extract, aggregator, flattenizer, default=default)
            elif isinstance(map_from, FlattenizerField):
                extractor = map_from
            else:
                extractor = compiled_flattenizer(map_from)

            if __debug__:
                setattr(
                    extractor, 'meta', {
                        'from': map_from, 'to': map_to, 'aggregator': aggregator
                    }
                )

            self._extractors[map_to] = extractor

    def for_source(self, source):
        return self._source_context(Getter(source, self))

    def getter(self, source):
        """
        Create Getter object with extractors in ._outer._extractors dict
        and the source in ._source dict
        :param source: source to write in Getter's ._source
        :return: Getter object
        """
        return Getter(source, self)

    def _get_item(self, item):
        """
        Push items from self._extractors
        :param item: item to get
        :return: item
        """
        return self._extractors[item]

    def _get_item_with_source(self, source, item):
        """
        Extract item with self._extractors from source
        :param source: source to extract
        :param item: item name
        :return:
        """
        try:
            return self._extractors[item](source)
        except _SkipError:
            return None

    @contextmanager
    def _source_context(self, getter):
        yield getter

    __getitem__ = _get_item


class Getter:
    """
    Suite for fast-getting filters and extract fields from the source
    """

    def __init__(self, source, outer):
        self._outer = outer
        self._source = source

    def __getitem__(self, item):
        """
        Push items from self._outer to self
        :param item: item name
        :return: item
        """
        return self._outer._get_item_with_source(self._source, item)

    def __getattribute__(self, item):
        """
        Push extractors' attributes from ._outer._extractor to self
        :param item: attribute name
        :return: attribute
        """
        if item in super().__getattribute__('_outer')._extractors:
            return self._outer._get_item_with_source(self._source, item)
        else:
            return super().__getattribute__(item)

    def extract(self, exclude=None):
        """
        Extract items from ._outer._extractors if not in exclude
        :param exclude: ._extractor's items to ignore
        :return:
        """
        def _exclude(f):
            if exclude is not None:
                return f in exclude
            else:
                return False
        res = {}
        for f in self._outer._extractors:
            if not _exclude(f):
                try:
                    k, v = f, self.__getitem__(f)
                except Exception:
                    raise BadRequest(description=f'Bad parameter "{f}" value')
                if v is not None:
                    res[k] = v
        return res


class FlattenizerModel(Getter):
    """
    TODO: Interpret field in metaclass, then instance model may be associated with data source, not with flatteniser
    >>> class Attachment(FlattenizerModel):
    ...     name = 'meta.name'
    ...     type = 'meta.type'
    ...     tags = 'meta.tags.*.name'
    ...     payload = 'payload'
    ...
    ... class MessageModel(FlattenizerModel):
    ...     recipients_names = 'result.recipients.*.name'
    ...     recipients_count = (len, 'result.recipients.*')
    ...     body = 'result.body'
    ...     attachments = (NestedList(Attachment), 'result.attachments')
    ...     def f(self):
    ...         pass
    ...
    ... ordinal_message = {
    ...     'result': {
    ...         'recipients': [{'name': 'Andrew'}, {'name': 'Vasya', 'second_name': 'Nikolaev'}],
    ...         'body': 'Message',
    ...         'attachments': [{'name': 'attach1'}, {'name': 'attach2'}]
    ...     }
    ... }
    ... message = MessageModel(ordinal_message)
    ... assert message.recipients_names == ['Andrew', 'Vasya']
    ... assert message.recipients_count == 2
    ... assert message.body == 'Message'
    ... assert message.attachments[0].name == 'Andrew'
    ... assert message.attachments[1].name == 'Andrew'
    """

    def __new__(cls, source):
        mapper_name = f'_mapper{cls.__name__}'
        if not hasattr(cls, mapper_name):
            mapping = chain(
                (
                    (field_name, field) for field_name, field in (
                    (f, getattr(cls, f)) for f in dir(cls) if not f.startswith('_')
                ) if (
                    not isinstance(field, FlattenizerModel) and
                    not isinstance(field, list) and
                    not isinstance(field, FunctionType)
                )
                )
            )
            mapper = FlattenizerMapper(mapping)
            setattr(cls, mapper_name, mapper)

        getter = Getter.__new__(cls)
        for field_name, nested_model in (
                (f, getattr(cls, f))
                for f in dir(cls) if isinstance(getattr(cls, f), NestedList)
        ):
            setattr(getter, field_name, nested_model(source))

        return getter

    def __init__(self, source):
        if isinstance(source, Getter):
            source = source.extract()
        super().__init__(source, getattr(type(self), f'_mapper{type(self).__name__}'))


class NestedList(object):
    """
    Nested list structure returns copy of ._model(source) if source items are acceptable
    """

    def __init__(self, model):
        self._model = model

    def __call__(self, source):
        assert isinstance(source, list)

        return [
            i for i in (
                self._model(item)
                for item in source
            ) if i is not None
        ]


def extract_values(source, mapping):
    """
    Extract values from the source with mapping
    :param source: extract from
    :param mapping: extract how
    :return:
    """
    mapped_source = lazy_flatten(source)

    res = {}
    for map_to, map_from in mapping.items():
        aggregator = None
        if isinstance(map_from, tuple):
            aggregator, map_from = map_from

        val = mapped_source[map_from]
        if val is None:
            continue

        if aggregator is not None:
            val = aggregator(val)

        res[map_to] = val

    return res


@clru_cache(maxsize=128)
def compiled_flattenizer(key, silent_key_error=True, silent_index_error=False):
    """
    Compile flattenizer with some cache for speedup
    :param key:
    :param silent_key_error:
    :param silent_index_error:
    :return:
    """

    def process_key_error(key, full_key=None):
        """
        Decide action on key error (silent_index_error for debug)
        :param key: param for error description
        :param full_key: param for error description
        :return:
        """
        if not silent_key_error:
            raise KeyMapError(f'{full_key[:full_key.find(key)+len(key)]}')
        else:
            raise _SkipError()

    def process_index_error(key, full_key=None):
        """
        Decide action on index error (silent_index_error for debug)
        :param key: param for error description
        :param full_key: param for error description
        :return:
        """
        if not silent_index_error:
            raise KeyMapError(f'{full_key[:full_key.find(key)+len(key)]}')
        else:
            raise _SkipError()

    def dict_expected_processor(key, full_key, got):
        """
        Raise dict expected error
        :param key: param for error description
        :param full_key: param for error description
        :param got: param for error description
        :return:
        """
        raise FlattenizerDictExpectedError(
            f'{full_key[:full_key.find(key)+len(key)]} got {type(got)}'
        )

    def list_expected_processor(key, full_key, got):
        """
        Raise list expected error
        :param key: param for error description
        :param full_key: param for error description
        :param got: param for error description
        :return:
        """
        raise FlattenizerListExpectedError(
            f'{full_key[:full_key.find(key)+len(key)]} got {type(got)}'
        )

    compiled = _compile_mapper(
        key, key, process_key_error, process_index_error,
        list_expected_processor, dict_expected_processor
    )

    if silent_index_error or silent_key_error:
        def wrap(*args, **kwargs):
            """
            Wrap for skipping _SkipError if one of silent flags present
            :param args:
            :param kwargs:
            :return:
            """
            try:
                res = compiled(*args, **kwargs)
                if isinstance(res, _SkipError):
                    return None
            except _SkipError:
                return None
            return res
    else:
        wrap = compiled

    return wrap


def _exc_as_rvalue(func, error_type):
    """
    Execute as row value
    :param func: func to execute
    :param error_type: error_type to except
    :return: result or error
    """

    def w(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except error_type as err:
            return err

    return w


class _SkipError(Exception):
    """
    Error to skip, neccessary for handling errors that we accept
    """
    pass


class _LazyFlattenizer(object):
    """
    Object to remember dict and error processing; and dynamically return item if exists
    (however, I did not see __getitem__ was called)
    """

    class _SkipListItem(Exception):
        pass

    def __init__(self, d, silent_key_error, silent_index_error):
        self.d = d
        self.silent_key_error = silent_key_error
        self.silent_index_error = silent_index_error

    def __getitem__(self, item):
        if not isinstance(item, str):
            raise ValueError('Mapped dict values can be accessed only with string keys')

        try:
            return compiled_flattenizer(
                item, self.silent_key_error, self.silent_index_error
            )(self.d)
        except _SkipError:
            return None


def _compile_mapper(
        key, full_key,
        key_error_processor, index_error_processor,
        list_expected_processor, dict_expected_processor
):
    """
    Recursive mapper compilator
    :param key: current key
    :param full_key: full key
    :param key_error_processor: function to call if key error
    :param index_error_processor: function to call if index error
    :param list_expected_processor: function to call if list expected
    :param dict_expected_processor: function to call if dict expected
    :return: function returns result dict
    """
    if ~key.find('.'):
        ckey, rest_key = key.split('.', 1)
        next_compiled = _compile_mapper(
            rest_key, full_key,
            key_error_processor, index_error_processor,
            list_expected_processor, dict_expected_processor
        )
    else:
        ckey = key
        next_compiled = None

    if next_compiled is None:
        def _process(node):
            return node
    else:
        def _process(node):
            return next_compiled(node)

    if ckey.isdigit():
        ckey = int(ckey)

        def _compiled(node):
            if not isinstance(node, list):
                return list_expected_processor(ckey, full_key)

            if len(node) < ckey:
                return index_error_processor(ckey, full_key)

            return _process(node[ckey])
    elif ckey == '*':
        def _compiled(node):
            if not isinstance(node, list):
                return list_expected_processor(ckey, full_key, node)

            res = [
                res for res in (
                    _exc_as_rvalue(
                        _process, _SkipError
                    )(item)
                    for item in node
                ) if not isinstance(res, _SkipError)
            ]
            if len(res) == 0:
                return _SkipError()
            return res
    else:
        def _compiled(node):
            if not isinstance(node, dict):
                return dict_expected_processor(ckey, full_key, node)

            if ckey not in node:
                return key_error_processor(ckey, full_key)

            return _process(node[ckey])

    return _compiled


def test_mapping():
    d = {
        'val': {
            'child': [
                {
                    'param': 10,
                    'nested_list': [
                        {
                            'nested_param': {
                                'param': 10
                            }
                        },
                        {
                            'nested_param': {
                                'param': 100
                            }
                        }
                    ]
                },
                {
                    'param': 100,
                    'nested_list': [
                        {
                            'nested_param': {
                                'param': 'value'
                            }
                        }
                    ]
                },
                {
                    'param': 1000
                }
            ]
        }
    }

    assert lazy_flatten(d)['val.child.*.param'] == [10, 100, 1000]
    assert lazy_flatten(d)['val.child.0.param'] == 10
    assert lazy_flatten(d)['val.child.1.param'] == 100
    assert lazy_flatten(d)['val.child.*.nested_list.*.nested_param.param'] == [
        [
            10, 100
        ],
        [
            'value'
        ]
    ]
    assert lazy_flatten(d)['val.child.0.nested_list.*.nested_param.param'] == [10, 100]


def test_values_extractor():
    mapping = {
        'extracted_value_1': 'vals.0.nested',
        'extracted_values': 'vals.*.nested',
        'summed': (sum, 'vals.*.nested'),
        'count': (len, 'vals.*')
    }
    source = {'vals': [{'nested': 1}, {'nested': 2}, {'nested': 3}, {'nested': 4}, {'noise': 1}]}
    flattenizer = FlattenizerMapper(mapping)
    assert flattenizer['extracted_values'](source) == [1, 2, 3, 4]
    assert flattenizer['extracted_value_1'](source) == 1
    assert flattenizer['summed'](source) == 10
    assert flattenizer['count'](source) == 5

    with flattenizer.for_source(source) as flat_source:
        assert flat_source['extracted_value_1'] == 1
        assert flat_source['extracted_values'] == [1, 2, 3, 4]
        assert flat_source['summed'] == 10
        assert flat_source['count'] == 5
        assert flat_source.extract() == {
            'extracted_value_1': 1,
            'extracted_values': [1, 2, 3, 4],
            'summed': 10,
            'count': 5
        }


class MessageModel(FlattenizerModel):
    recipients_names = 'result.recipients.*.name'
    recipients_count = (len, 'result.recipients.*')
    body = 'result.body'
    attachments = 'result.attachments'

    def f(self):
        pass


ordinal_message = {
    'result': {
        'recipients': [{'name': 'Andrew'}, {'name': 'Vasya', 'second_name': 'Nikolaev'}],
        'body': 'Message',
        'attachments': [
            {'meta': {'name': 'attach1'}}, {'meta': {'name': 'attach2'}}
        ]
    }
}

ordinal_message2 = {
    'result': {
        'recipients': [{'name': 'Andrew'}, {'name': 'Vasya', 'second_name': 'Nikolaev'}],
        'body': 'Message'
    }
}


def test_model():
    message = MessageModel(ordinal_message)
    assert message['recipients_names'] == ['Andrew', 'Vasya']
    assert message['recipients_count'] == 2
    assert message['body'] == 'Message'
    assert message['attachments'] == [{'meta': {'name': 'attach1'}}, {'meta': {'name': 'attach2'}}]


def test_inherited_model():
    class InheritedMessageModel(MessageModel):
        recipients_second_names = 'result.recipients.*.second_name'

    message = InheritedMessageModel(ordinal_message)
    assert message['recipients_names'] == ['Andrew', 'Vasya']
    assert message['recipients_count'] == 2
    assert message['body'] == 'Message'
    assert message['attachments'] == [{'meta': {'name': 'attach1'}}, {'meta': {'name': 'attach2'}}]
    assert message['recipients_second_names'] == ['Nikolaev']


def test_model_instance_attribute():
    class Attachment(FlattenizerModel):
        name = 'meta.name'
        type = 'meta.type'
        tags = 'meta.tags.*.name'
        payload = 'payload'

    class MessageModel(FlattenizerModel):
        recipients_names = 'result.recipients.*.name'
        recipients_count = (len, 'result.recipients.*')
        title = 'result.title'
        body = 'result.body'
        attachments = (NestedList(Attachment), 'result.attachments')

    message = MessageModel(ordinal_message)
    assert message.recipients_names == ['Andrew', 'Vasya']
    assert message.recipients_count == 2
    assert message.body == 'Message'
    assert message.title is None
    assert message.attachments[0].name == 'attach1'
    assert message.attachments[1].name == 'attach2'
    assert message.attachments[0].type is None


def test_model_with_fields_instance_attribute():
    class Attachment(FlattenizerModel):
        name = FlattenizerField('meta.name')
        type = FlattenizerField('meta.type')
        tags = FlattenizerField('meta.tags.*.name')
        payload = FlattenizerField('payload', 'example')

    class MessageModel(FlattenizerModel):
        recipients_names = FlattenizerField('result.recipients.*.name')
        recipients_count = FlattenizerField('result.recipients.*', len)
        title = FlattenizerField('result.title')
        body = FlattenizerField('result.body')
        attachments = FlattenizerField('result.attachments', Attachment, default=[])

    message = MessageModel(ordinal_message)
    assert message.recipients_names == ['Andrew', 'Vasya']
    assert message.recipients_count == 2
    assert message.body == 'Message'
    assert message.title is None
    assert message.attachments[0].name == 'attach1'
    assert message.attachments[1].name == 'attach2'
    assert message.attachments[0].type is None
    # assert message.attachments[0].payload == 'example'
    # assert message.attachments[1].payload == 'example'

    message = MessageModel(ordinal_message2)
    assert message.attachments == []
