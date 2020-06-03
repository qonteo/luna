from app.version import VERSION
from app.handlers.base_handler import BaseRequestHandler


class VersionHandler(BaseRequestHandler):
    """
    Handler for getting version
    """

    def get(self):
        """
        Resource is reached by address '/version'

        .. http:get:: /version

            Request to receive service version

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 200 OK
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295

            .. json:object:: luna_image_store_version

                :property api: number of api version
                :proptype api: integer
                :property major: number of major version
                :proptype major: integer
                :property minor: number of major version
                :proptype minor: integer
                :property patch: number of patch version
                :proptype patch: integer

            .. json:object:: response normal version
                :showexample:

                :property Version: version of server
                :proptype Version: luna_image_store_version

            .. sourcecode:: http

                HTTP/1.1 200
                Begin-Request-Time: 1526039272.9173293
                End-Request-Time: 1526039272.9505265
                LUNA-Request-Id: 1516179740,af3fb041-1a55-43e6-9ac2-a361aa43295f
                Content-Type: application/json

            :statuscode 200: Ok
            :statuscode 500: internal server error
        """
        return self.success(statusCode=200, outputJson=VERSION)
