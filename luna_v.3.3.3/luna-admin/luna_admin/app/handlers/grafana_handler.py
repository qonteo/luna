"""
Module realize handler for getting url to grafana with dashboards
"""
from tornado import web

from app.handlers.base_handler import BaseHandlerWithAuth
from configs.config import GRAFANA_ORIGIN


class GrafanaHandler(BaseHandlerWithAuth):
    """
    Grafana settings handler.
    """

    @BaseHandlerWithAuth.requestExceptionWrap
    def get(self) -> None:
        """

        Get grafana service.

        .. http:get:: /grafana


            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d


                .. json:object:: grafana
                    :showexample:

                    :property url grafana_url: url to grafana
                    :proptype grafana_url: :json:object:`admin_db`


            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """

        return self.success(200, outputJson={
            "grafana_url": GRAFANA_ORIGIN if GRAFANA_ORIGIN is not None else "grafana server does not set"
        })
