import unittest

import itertools


class CollectFieldsIntoClassAttribute(type):
    """
    This metaclass lists all declared fields in the class (and all base classes) and puts them into `attribute_name` class attribute. Classes are instances of `allow_instances` class or subclasses of `allow_subclasses`. 
	`attribute_name` is represented by dictionary, where keys are field names, values are field values.
	Optionally apply `name_field_func: Callable[Any, str]` to name all the fields.
    Also set `__field_attribute_name__` on the class which is `attribute_name`

    Support inheritance, but note: all parameters and fields will be picked from first base class, which have same metaclass.
    # TODO Support multi bases with same metaclass
     Example:
         >>> class Field:
         ... def __init__(self, name=None):
         ...     self.name = name
         ...
         ... def set_name(self, name):
         ...     self.name = name
         ...
         ... class Model(
         ...   metaclass=CollectFieldsIntoClassAttribute,
         ...   attribute_name='fields', allow_instances=Field,
         ...   name_field_func=Field.set_name
         ... ):
         ...   field1 = Field()
         ...   field2 = Field()
         ...
         ... print(Model.fields)
         {'field1': Field field1, 'field2': Field field2}

    """

    def __new__(
        mcs, name, bases, fields, attribute_name=None,
        allow_subclasses=None, allow_instances=None,
        name_field_func=None
    ):
        # look for base classes which are produced with this metaclass
        meta_bases = [
            b for b in bases
            if isinstance(b, CollectFieldsIntoClassAttribute)
        ]
        # get items of fields in base classes
        if len(meta_bases) > 0:
            first_base = meta_bases[0]
            if attribute_name is None:
                attribute_name = first_base.__field_attribute_name__
            if name_field_func is None and first_base.__name_field_func__ is not None:
                name_field_func = first_base.__name_field_func__
            if allow_subclasses is None and first_base.__allow_subclasses__ is not None:
                allow_subclasses = first_base.__allow_subclasses__
            if allow_instances is None and first_base.__allow_instances__ is not None:
                allow_instances = first_base.__allow_instances__

            first_base_fields = getattr(
                first_base, first_base.__field_attribute_name__
            ).items()
        else:
            first_base_fields = []
        # checks
        if allow_subclasses is not None and allow_instances is not None:
            raise ValueError('Either "allow_subclasses" or "allow_instances" are required!')
        if attribute_name is None:
            raise ValueError('"attribute_name" is required')
        # chain fields' and bases' __dict__s items
        selected_fields = itertools.chain(
            fields.items(), first_base_fields,
            itertools.chain.from_iterable(
                b.__dict__.items() for b in bases
                if not isinstance(b, CollectFieldsIntoClassAttribute)
            )
        )
        # filter from selected_fields if values are subclasses
        if allow_subclasses is not None:
            selected_fields_subclasses = (
                (name, value)
                for name, value in selected_fields
                if isinstance(value, type) and issubclass(value, allow_subclasses)
            )
        else:
            selected_fields_subclasses = []

        # filter from selected_fields if values are instances
        if allow_instances is not None:
            selected_fields_instances = (
                (name, value)
                for name, value in selected_fields
                if isinstance(value, allow_instances)
            )
        else:
            selected_fields_instances = []

        # get one of them as list
        selected_fields = list(selected_fields_instances) + list(selected_fields_subclasses)

        # name fields if function is provided
        if name_field_func is not None:
            for name, field in selected_fields:
                name_field_func(field, name)

        # save all the fields to attribute_name
        fields[attribute_name] = dict(selected_fields)
        # save meta fields
        fields['__field_attribute_name__'] = attribute_name
        fields['__allow_subclasses__'] = allow_subclasses
        fields['__allow_instances__'] = allow_instances
        fields['__name_field_func__'] = name_field_func

        return super().__new__(mcs, name, bases, fields)


class TestCase(unittest.TestCase):
    def test_field_instances(self):
        class Field:
            def __init__(self, name=None):
                self.name = name

            def set_name(self, name):
                self.name = name

            def __repr__(self):
                return f'Field {self.name}'

            def __eq__(self, other):
                return self.name == other.name

        class Test(
            metaclass=CollectFieldsIntoClassAttribute,
            attribute_name='fields', allow_instances=Field,
            name_field_func=Field.set_name
        ):
            field1 = Field()
            field2 = Field()

        self.assertEqual(
            Test.fields,
            {
                'field1': Field('field1'),
                'field2': Field('field2')
            }
        )
        self.assertEqual(
            Test.__field_attribute_name__, 'fields'
        )
        self.assertIs(
            Test.__allow_subclasses__, None
        )
        self.assertIs(
            Test.__allow_instances__, Field
        )
        self.assertIs(
            Test.__name_field_func__, Field.set_name
        )

    def test_field_classes(self):
        class Field:
            pass

        class AField(Field):
            pass

        class BField(Field):
            pass

        class Test(
            metaclass=CollectFieldsIntoClassAttribute,
            attribute_name='fields', allow_subclasses=Field,
        ):
            field1 = AField
            field2 = BField

    def test_inheritance(self):
        self.maxDiff = None

        class Field:
            def __init__(self, name=None):
                self.name = name

            def set_name(self, name):
                self.name = name

            def __eq__(self, other):
                return self.name == other.name

        class Base(
            metaclass=CollectFieldsIntoClassAttribute,
            attribute_name='fields', allow_instances=Field,
            name_field_func=Field.set_name
        ):
            base_field1 = Field()
            base_field2 = Field()

        class Derived(Base):
            field1 = Field()
            field2 = Field()

        self.assertEqual(
            Derived.fields,
            {
                'base_field1': Field('base_field1'),
                'base_field2': Field('base_field2'),
                'field1': Field('field1'),
                'field2': Field('field2')
            }
        )
