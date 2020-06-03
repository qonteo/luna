from common.inflixdb_query_builder import (
    InfluxDBTypesChecker, BaseFilterConditionBuilder, InfluxDBQueryBuilder, ThresholdFilterConditionBuilder
)


class StatQueryBuilder(InfluxDBQueryBuilder):
    EVENT_TYPE_TO_SERIES = {
        'match': 'match_series',
        'extract': 'extract_series'
    }

    class FilterModel:
        """
        Static request parameters' parse model
        """
        time = BaseFilterConditionBuilder(
            InfluxDBTypesChecker.create_timestamp, ('lt', 'gt'),
            default_condition=('gt', 'now - 3h')
        )
        account_id = BaseFilterConditionBuilder(
            InfluxDBTypesChecker.create_str, ('eq',),
            required=True
        )
        event_type = BaseFilterConditionBuilder(
            InfluxDBTypesChecker.create_event_type, ('eq',),
            required=True
        )
        authorization = BaseFilterConditionBuilder(
            InfluxDBTypesChecker.create_re, ('mp',)
        )
        source = BaseFilterConditionBuilder(
            InfluxDBTypesChecker.create_str, ('eq',)
        )
        list = BaseFilterConditionBuilder(
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
            InfluxDBTypesChecker.create_float, ('lt', 'gt'),
            {
                'event_type': lambda value: value == 'match'
            }
        )

    def _get_series_name(self):
        event_type = self._filters['event_type']
        return self.EVENT_TYPE_TO_SERIES[event_type]
