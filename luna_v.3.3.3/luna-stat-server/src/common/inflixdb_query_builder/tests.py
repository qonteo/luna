import unittest
from collections import OrderedDict

from common.inflixdb_query_builder.generic_builder import InfluxDBQueryBuilder, IDBQueryBuilderError, InfluxDBTypesChecker,    BaseFilterConditionBuilder, ThresholdFilterConditionBuilder


class InfluxDBQueryBuilderTestCase(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

        class StatQueryBuilder(InfluxDBQueryBuilder):
            class FilterModel:
                time = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_timestamp, ('lt', 'gt'),
                    default_condition=('gt', 'now - 3h')
                )
                account_id = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_str, ('eq',)
                )
                event_type = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_event_type, ('eq',)
                )
                auth_type = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_str, ('eq',)
                )
                source = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_str, ('eq',)
                )
                face_score = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('gt',)
                )
                age = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('lt', 'gt')
                )
                gender = ThresholdFilterConditionBuilder(
                    ['female', 'male'], 0.5
                )
                skin_color = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('lt', 'gt')
                )
                over_exposed = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('lt', 'gt')
                )
                glasses = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('lt', 'gt')
                )
                similarity = BaseFilterConditionBuilder(
                    InfluxDBTypesChecker.create_float, ('gt',),
                    {
                        'event_type': lambda value: value == 'match'
                    }
                )

        self.qb = StatQueryBuilder()

    def test_case1(self):
        self.qb.set_series_name('match_series')
        self.assertEqual(
            self.qb.build(),
            'SELECT max(*) FROM "match_series"  GROUP BY time(1h) fill(none)'
        )

    def test_case2(self):
        self.qb.set_series_name('match_series')
        self.qb.apply_filters(
            OrderedDict(
                {
                    'account_id': 'ac1',
                    'similarity__gt': 0.4,
                    'time__gt': 'now -3h',
                    'event_type': 'match'
                }
            )
        )
        self.qb.set_fields(['face_score', 'similarity'])

        self.assertEqual(
            self.qb.build(),
            'SELECT max("face_score"), max("similarity") '
            'FROM "match_series" '
            'WHERE '
                '"account_id" = \'ac1\' AND '
                '"similarity" > 0.4 AND '
                '"time" > now() - 3h AND '
                '"event_type" = \'match\' '
            'GROUP BY time(1h) fill(none)'
        )

    def test_case3(self):
        self.qb.set_series_name('match_series')
        self.qb.apply_filters(
            OrderedDict(
                {
                    'account_id': 'ac1',
                    'event_type': 'match',
                    'gender': 'male'
                }
            )
        )
        self.assertEqual(
            self.qb.build(),
            'SELECT max(*) '
            'FROM "match_series" '
            'WHERE '
                '"account_id" = \'ac1\' AND '
                '"event_type" = \'match\' AND '
                '"gender" >= 0.5 AND '
                '"time" > now() - 3h '
            'GROUP BY time(1h) fill(none)'
        )

    def test_case4(self):
        self.qb.set_series_name('match_series')
        self.qb.apply_filters(
            {
                'event_type': 'match',
                'gender': 'female',
                'account_id': 'ac1',
                'similarity__gt': 0.4,
                'time__gt': 'now -3d'
            }
        )
        self.assertEqual(
            self.qb.build(),
            'SELECT max(*) '
            'FROM "match_series" '
            'WHERE '
                '"event_type" = \'match\' AND '
                '"gender" < 0.5 AND '
                '"account_id" = \'ac1\' AND '
                '"similarity" > 0.4 AND '
                '"time" > now() - 3d '
            'GROUP BY time(1h) fill(none)'
        )


if __name__ == '__main__':
    unittest.main()
