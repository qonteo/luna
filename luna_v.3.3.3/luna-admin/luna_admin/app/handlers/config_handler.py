"""
Module realize handler for getting service configuration.
"""
from app.handlers.base_handler import BaseHandlerWithAuth
from configs import config


class ConfigHandler(BaseHandlerWithAuth):
    """
    Admin configs handler.
    """

    def get(self) -> None:
        """

        Get configuration.

        .. http:get:: /config


            :reqheader Authorization: basic authorization

            **Example response**:

                .. sourcecode:: http

                    HTTP/1.1 200 Ok
                    Vary: Accept
                    Content-Type: application/json
                    LUNA-Request-Id: 1516179740,d3abc2f6-70f1-4ae0-9d10-475103e0891d

                .. json:object:: admin_db

                    :property type: database type
                    :proptype type: _enum_(oracle)_(postgres)
                    :property ipv4 host: database host
                    :property integer port: database port
                    :property user_name db_name: database name
                    :property user_name user_name: user name

                .. json:object:: statistic_db

                    :property ipv4 host: database host
                    :proptype user_name db_name: database name
                    :property url grafana_url: grafana url

                .. json:object:: gc

                    :property integer ttl: time to live  free descriptors

                .. json:object:: common

                    :property log_level:  level of debug print, by priority
                    :proptype log_level: _enum_(ERROR)_(DEBUG)_(WARNING)_(INFO)
                    :property log_time:  time for records in logs
                    :proptype log_time: _enum_(UTC)_(LOCAL)
                    :property integer connection_timeout: connection timeout
                    :property integer request_timeout: request timeout
                    :property string folders_with_log: folder, where logs are saved

                .. json:object:: luna_core

                    :property url origin: origin
                    :property integer api_version: api version

                .. json:object:: admin_tasks_server

                    :property url origin: admin tasks server origin

                .. json:object:: image_store_warps

                    :property url origin: image store warps origin
                    :property integer api_version: image store warps api version
                    :property user_name bucket: image store warps bucket

                .. json:object:: image_store_portraits

                    :property save_portraits: image store portraits origin
                    :proptype save_portraits: _enum_(1_0)
                    :property url origin: image store portraits origin
                    :property integer api_version: image store portraits api version
                    :property user_name bucket: image store portraits bucket



                .. json:object:: settings
                    :showexample:

                    :property admin_db: admin db settings
                    :proptype admin_db: :json:object:`admin_db`
                    :property luna_api_db: luna-api db settings
                    :proptype luna_api_db: :json:object:`admin_db`
                    :property statistic_db: statistics db settings
                    :proptype statistic_db: :json:object:`account_stats`
                    :property gc: admin db settings
                    :proptype gc: :json:object:`gc`
                    :property common: common settings
                    :proptype common: :json:object:`common`
                    :property luna_core: core settings
                    :proptype luna_core: :json:object:`luna_core`
                    :property luna_core_reextract: core reextract settings
                    :proptype luna_core_reextract: :json:object:`luna_core`
                    :property luna_faces: luna faces settings
                    :proptype luna_faces: :json:object:`luna_core`
                    :property admin_tasks_server: admin tasks server settings
                    :proptype admin_tasks_server: :json:object:`admin_tasks_server`
                    :property luna_image_store_warped_images: luna image store warps server bucket
                    :proptype luna_image_store_warped_images: :json:object:`image_store_warps`
                    :property luna_image_store_portraits: luna image store portraits server bucket
                    :proptype luna_image_store_portraits: :json:object:`image_store_portraits`


            Message error is returned in format :json:object:`server_error`.

            :statuscode 200: success
            :statuscode 400: Bad query parameters
            :statuscode 500: internal server error
        """
        adminDB = {
            "type": config.ADMIN_DB_TYPE,
            "host": config.ADMIN_DB_HOST,
            "port": config.ADMIN_DB_PORT,
            "db_name": config.ADMIN_DB_NAME,
            "user_name": config.ADMIN_DB_USER_NAME,
        }
        lunaApiDb = {
            "type": config.LUNA_API_DB_TYPE,
            "host": config.LUNA_API_DB_HOST,
            "port": config.LUNA_API_DB_PORT,
            "db_name": config.LUNA_API_DB_NAME,
            "user_name": config.LUNA_API_DB_USER_NAME,
        }
        statisticDb = {
            "host": config.ADMIN_STATISTICS_SERVER_ORIGIN,
            "db_name": config.ADMIN_STATISTICS_DB,
            "grafana_url": config.GRAFANA_ORIGIN
        }

        gcSettings = {
            "ttl": config.TTL_DESCRIPTOR,
        }
        common = {
            "log_level": config.LOG_LEVEL,
            "log_time": config.LOG_TIME,
            "connection_timeout": config.CONNECT_TIMEOUT,
            "request_timeout": config.REQUEST_TIMEOUT,
            "folders_with_log": config.FOLDER_WITH_LOGS
        }
        lunaCore = {"origin": config.LUNA_CORE_ORIGIN, "api_version": config.LUNA_CORE_API_VERSION}
        lunaFaces = {"origin": config.LUNA_FACES_ORIGIN, "api_version": config.LUNA_FACES_API_VERSION}
        lunaCoreReextract = {
            "origin": config.LUNA_CORE_REEXTRACT_ORIGIN,
            "api_version": config.LUNA_CORE_REEXTRACT_API_VERSION
        }
        adminTasksServer = {"origin": config.ADMIN_TASKS_SERVER_ORIGIN}
        lunaImageStoreWarps = {
            "origin": config.LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN,
            "api_version": config.LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION,
            "bucket": config.LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET
        }

        lunaImageStorePortraits = {
            "save_portraits": config.SEND_TO_LUNA_IMAGE_STORE,
            "origin": config.LUNA_IMAGE_STORE_PORTRAITS_ORIGIN,
            "api_version": config.LUNA_IMAGE_STORE_PORTRAITS_API_VERSION,
            "bucket": config.LUNA_IMAGE_STORE_PORTRAITS_BUCKET
        }
        settings = {
            "admin_db": adminDB,
            "luna_api_db": lunaApiDb,
            "statistic_db": statisticDb,
            "gc": gcSettings,
            "common": common,
            "luna_core": lunaCore,
            "luna_core_reextract": lunaCoreReextract,
            "luna_faces": lunaFaces,
            "admin_tasks_server": adminTasksServer,
            "luna_image_store_warped_images": lunaImageStoreWarps,
            "luna_image_store_portraits": lunaImageStorePortraits
        }
        self.success(200, outputJson=settings)
