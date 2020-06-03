import tornado.web
from tornado import gen
import ujson as json
from version import VERSION
from app.rest_handlers.base_handler_class import BaseRequestHandler


class VersionHandler(BaseRequestHandler):
    """
    Handler for luna_python_server version
    """
    @tornado.web.asynchronous
    @BaseRequestHandler.requestExceptionWrap
    @gen.coroutine
    def get(self):
        """
        Resource is reached by address '/version'

        .. http:get:: /version

        Request to receive service version

        :reqheader LUNA-Request-Id: request id

        **Example response**:

        .. sourcecode:: http

            HTTP/1.1 200 OK
            Vary: Accept
            Content-Type: application/json
            LUNA-Request-Id: 1516179740,c06887a2

        .. json:object:: luna_api_version

            :property api: number of api version
            :proptype api: integer
            :property major: number of major version
            :proptype major: integer
            :property minor: number of major version
            :proptype minor: integer
            :property patch: number of patch version
            :proptype patch: integer

        .. json:object:: version

            :property major: number of major version
            :proptype major: integer
            :property minor: number of major version
            :proptype minor: integer
            :property patch: number of patch version
            :proptype patch: integer

        .. json:object:: luna_core_version

            :property fsdk: version of fsdk
            :proptype fsdk: :json:object:`version`
            :property api: number of api version
            :proptype api: integer
            :property luna: version of fsdk
            :proptype luna: :json:object:`version`

        .. json:object:: all_versions

            :property luna_api: version of luna api
            :proptype luna_api: luna_api_version
            :property luna_core: version of luna core
            :proptype luna_core: luna_core_version

        .. json:object:: response normal version
            :showexample:

            :property Version: version of server
            :proptype Version: all_versions

        :statuscode 200: Version successfully received, if versioning was unsuccessful, version\
         will have value "UNKNOWN"
        :statuscode 500:  Exception caught
        """

        lunaVersionRes = yield self.lunaCoreContext.getLunaVersion()
        self.set_header('Content-Type', 'application/json')

        self.set_status(200)
        self.finish(json.dumps({"Version": {
                                "luna_api": VERSION["Version"],
                                "luna_core": lunaVersionRes}}))
