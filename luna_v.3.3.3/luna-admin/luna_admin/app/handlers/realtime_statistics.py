"""
Admin stats handler
"""
import requests
from influxdb.client import InfluxDBClient
from configs import config
from app.handlers.base_handler import BaseHandlerWithAuth
from app.handlers.statistic_helpers import prepare_params
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from tzlocal import get_localzone

_, IP, PORT = config.ADMIN_STATISTICS_SERVER_ORIGIN.split(':')
IP = IP[2:]
influxClient = InfluxDBClient(IP, database=config.ADMIN_STATISTICS_DB, port=int(PORT), timeout=60)


class RealtimeStatisticsHandler(BaseHandlerWithAuth):
    """
    Admin stats handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self, series: str) -> None:
        """
        Search element by id or email.

        .. http:get:: /realtime_statistics/{series}


            :param series: extract_success|matching_success|errors
            :query resource: resource to get statistics about. Will be ignored if not set.
                             ("descriptors", "search", "match", "identify", "verify")
            :query error: luna API error code to get statistics about
            :query aggregator: aggregation type ("max", "min", "mean", "count")
            :query count_faces: result count faces on photo
            :query limit: matching limit in match request
            :query template: template in match request. 1 - person, 0 - descriptor
            :query candidate: candidate in match request. 1 - dynamic list, 0 - static Luna API list

            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: stats result
                    :showexample:

                    :property name:  The name of current series
                    :proptype name: _enum_(extract_success)_(matching_success,errors)
                    :property columns: Titles of cells in values' batches
                    :property values: List of values' batches

            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """

        paramsRes = prepare_params(self.get_query_argument, series)
        if paramsRes.fail:
            error = Error.generateError(paramsRes.error,
                                        paramsRes.value)
            raise VLException(error, 400, isCriticalError=False)
        params = paramsRes.value

        query = "SELECT {aggregator}(*) FROM {series}  WHERE {time__gte} < time AND time < {time__lt} {where} group by time({group_by}) fill(none)".format(
            **params)
        try:
            res = influxClient.query(query + " TZ('{}')".format(get_localzone()))
        except requests.exceptions.ConnectionError:
            raise VLException(Error.InfluxConnectionTimeout, 500, False)

        return self.success(200, outputJson=res.raw['series'][0] if 'series' in res.raw else {})
