# -*- coding: utf-8 -*-
"""
В данном файле собраны настройки для работы системы.
"""
import os
import tornado.options
from tornado.options import define, options
import sys
from configs.comand_line_args_parser import getOptionsParser


def setPythonPathToAPP():
    """
    Set python path to root of app.
    """
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__) + "/../", os.path.pardir)))
    os.chdir(os.path.join(os.path.dirname(__file__) + "/../"))


def replacePythonPathIfNeed():
    """
    Determinate need set python path to root or not

    If run sphinx, db_create, influx_db_create, db_migrate set python path to root app.
    """
    if sys.argv[0].find("sphinx") > 0 or sys.argv[0].find("db_create") > 0 or sys.argv[0].find("influx_db_create") \
            or sys.argv[0].find("create_grafana_dashboards") > 0 or sys.argv[0].find("db_migrate"):
        setPythonPathToAPP()


replacePythonPathIfNeed()

define("LUNA_API_DB_TYPE", default="postgres", help="type of database: postgres, oracle, default postgres")
define("LUNA_API_DB_USER_NAME", default="faceis", help="login to database")
define("LUNA_API_DB_PASSWORD", default="faceis", help="password to database")
define("LUNA_API_DB_HOST", default="127.0.0.1", help="ip-address of database")
define("LUNA_API_DB_PORT", default=5432,
       help="database listener port, 5432 - default port of postgres, 1521 - default port of oracle")
define("LUNA_API_DB_NAME", default="faceis_db", help="name of database for postgres, sid name for oracle")

define("ADMIN_DB_TYPE", default="postgres", help="type of database: postgres, oracle, default postgres")
define("ADMIN_DB_USER_NAME", default="faceis", help="login to database")
define("ADMIN_DB_PASSWORD", default="faceis", help="password to database")
define("ADMIN_DB_HOST", default="127.0.0.1", help="ip-address of database")
define("ADMIN_DB_PORT", default=5432,
       help="database listener port, 5432 - default port of postgres, 1521 - default port of oracle")
define("ADMIN_DB_NAME", default="admin_faceis_db", help="name of database for postgres, sid name for oracle")

define("LUNA_CORE_ORIGIN", default="http://127.0.0.1:8083", help="LUNA Core origin")
define("LUNA_CORE_API_VERSION", default=14, help="LUNA Core api version")

define("LUNA_CORE_REEXTRACT_ORIGIN", default="http://127.0.0.1:8083",
       help="origin of LUNA Core with new type of descriptors")
define("LUNA_CORE_REEXTRACT_API_VERSION", default=14, help="api version of LUNA Core with new type of descriptors")

define("LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN", default="http://127.0.0.1:5020", help="luna-image-store origin")
define("LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION", default=1, help="luna-image-store api version")
define("LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET", default="visionlabs-warps", help="luna-image-store bucket")

define("SEND_TO_LUNA_IMAGE_STORE", default=1, help="save portrait to luna-image-store")
define("LUNA_IMAGE_STORE_PORTRAITS_ORIGIN", default="http://127.0.0.1:5020",
       help="origin of service for storing portraits from LUNA Api")
define("LUNA_IMAGE_STORE_PORTRAITS_API_VERSION", default=1, help="luna-image-store api version for portraits")
define("LUNA_IMAGE_STORE_PORTRAITS_BUCKET", default="visionlabs-portraits", help="luna-image-store bucket for portraits")

define("LUNA_FACES_ORIGIN", default="http://127.0.0.1:5030", help="luna-faces origin")
define("LUNA_FACES_API_VERSION", default=1, help="luna-faces api version")

define("ADMIN_STATISTICS_SERVER_ORIGIN", default="http://127.0.0.1:8086", help="Admin statistic host host")

define("LOG_LEVEL", default="INFO", help="log level")

define("ADMIN_STATISTICS_DB", default="luna_api_admin", help="Influx database")
define("FOLDER_WITH_LOGS", default="./", help="Folder with logs")

define("GRAFANA_ORIGIN", help="Grafana server")

define("TTL_DESCRIPTOR", default=1, help="ttl of free descriptors (in days)")

define("TIMEOUT_GC_DESCRIPTORS", default=7, help="timeout for descriptors gc (in days)")

define("LOG_TIME", default="LOCAL", help="time for records in logs: LOCAL or UTC")

define("ADMIN_TASKS_SERVER_ORIGIN", default="http://127.0.0.1:5011", help="service for long task")

define("APP_NAME", default="luna-admin", help="application name")

define("REQUEST_TIMEOUT", type=int, default=60, help="Request timeout to internal services")
define("CONNECT_TIMEOUT", type=int, default=30, help="Connect timeout to internal services")

define("ADMIN_REQUEST_TIMEOUT", type=int, default=60, help="Request timeout to luna-admin service")
define("ADMIN_CONNECT_TIMEOUT", type=int, default=30, help="Connect timeout to luna-admin service")

cmdOptions = getOptionsParser()
tornado.options.parse_config_file(cmdOptions["config"])

basedir = os.path.abspath(os.path.dirname(__file__)) + "/../"
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

#: type of database: postgres, oracle, default postgres
LUNA_API_DB_TYPE = options.LUNA_API_DB_TYPE
#: postgresql login for postgresql Luna API
LUNA_API_DB_USER_NAME = options.LUNA_API_DB_USER_NAME
#: postgresql password for postgresql Luna API
LUNA_API_DB_PASSWORD = options.LUNA_API_DB_PASSWORD
#: ip-address of postgresql with Luna API
LUNA_API_DB_HOST = options.LUNA_API_DB_HOST
#: port of postgresql with Luna API
LUNA_API_DB_PORT = options.LUNA_API_DB_PORT
#: name of database for Luna API
LUNA_API_DB_NAME = options.LUNA_API_DB_NAME

if LUNA_API_DB_TYPE == "postgres":
    LUNA_API_DB_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
        LUNA_API_DB_USER_NAME, LUNA_API_DB_PASSWORD, LUNA_API_DB_HOST, LUNA_API_DB_PORT, LUNA_API_DB_NAME
    )  #: postgresql address
elif LUNA_API_DB_TYPE == "oracle":
    LUNA_API_DB_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(
        LUNA_API_DB_USER_NAME, LUNA_API_DB_PASSWORD, LUNA_API_DB_HOST, LUNA_API_DB_PORT, LUNA_API_DB_NAME
    )  #: oracle address
else:
    raise ValueError("Bad DB name: {}, supports: postgres or oracle".format(LUNA_API_DB_TYPE))

#: type of database: postgres, oracle, default postgres
ADMIN_DB_TYPE = options.ADMIN_DB_TYPE
#: login to database
ADMIN_DB_USER_NAME = options.ADMIN_DB_USER_NAME
#: password to database
ADMIN_DB_PASSWORD = options.ADMIN_DB_PASSWORD
#: name of database for postgres, sid name for oracle
ADMIN_DB_NAME = options.ADMIN_DB_NAME
#: ip-address of database
ADMIN_DB_HOST = options.ADMIN_DB_HOST
#: database listener port, 5432 - default port of postgres, 1521 - default port of oracle
ADMIN_DB_PORT = options.ADMIN_DB_PORT

if ADMIN_DB_TYPE == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(
        ADMIN_DB_USER_NAME, ADMIN_DB_PASSWORD, ADMIN_DB_HOST, ADMIN_DB_PORT, ADMIN_DB_NAME
    )  #: postgresql address
elif ADMIN_DB_TYPE == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(
        ADMIN_DB_USER_NAME, ADMIN_DB_PASSWORD, ADMIN_DB_HOST, ADMIN_DB_PORT, ADMIN_DB_NAME
    )  #: oracle address
else:
    raise ValueError("Bad DB name: {}, supports: postgres or oracle".format(ADMIN_DB_TYPE))

#: flag, which indicates whether send portraits to LUNA Image Store or not
SEND_TO_LUNA_IMAGE_STORE = options.SEND_TO_LUNA_IMAGE_STORE
#: origin of LUNA Image Store
LUNA_IMAGE_STORE_PORTRAITS_ORIGIN = options.LUNA_IMAGE_STORE_PORTRAITS_ORIGIN
#: api version of LUNA Image Store
LUNA_IMAGE_STORE_PORTRAITS_API_VERSION = options.LUNA_IMAGE_STORE_PORTRAITS_API_VERSION
#: name *bucket*, where portraits will be stored
LUNA_IMAGE_STORE_PORTRAITS_BUCKET = options.LUNA_IMAGE_STORE_PORTRAITS_BUCKET

#: LUNA Image Store origin
LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN = options.LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN
#: LUNA Image Store api version
LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION = options.LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION
#: name *bucket*, where warped images will be stored
LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET = options.LUNA_IMAGE_STORE_WARPED_IMAGES_BUCKET

#: LUNA Faces origin
LUNA_FACES_ORIGIN = options.LUNA_FACES_ORIGIN
#: LUNA Faces api version
LUNA_FACES_API_VERSION = options.LUNA_FACES_API_VERSION

#: LUNA Core origin
LUNA_CORE_REEXTRACT_ORIGIN = options.LUNA_CORE_REEXTRACT_ORIGIN
#: LUNA Core api version
LUNA_CORE_REEXTRACT_API_VERSION = options.LUNA_CORE_REEXTRACT_API_VERSION

#: origin of LUNA Core with new type of descriptors
LUNA_CORE_ORIGIN = options.LUNA_CORE_ORIGIN
#: api version of LUNA Core with new type of descriptors
LUNA_CORE_API_VERSION = options.LUNA_CORE_API_VERSION

#: level of debug print, by priority: ERROR, WARNING, INFO, DEBUG
LOG_LEVEL = options.LOG_LEVEL

#: Influxdb server, where statistics is collected from LUNA API
ADMIN_STATISTICS_SERVER_ORIGIN = options.ADMIN_STATISTICS_SERVER_ORIGIN
#: Base with time series for administrator statistics from LUNA API
ADMIN_STATISTICS_DB = options.ADMIN_STATISTICS_DB
#: Grafana server  for visualized statistics
GRAFANA_ORIGIN = options.GRAFANA_ORIGIN

#: folder, where logs are saved
FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS

#: time to live free descriptors
TTL_DESCRIPTOR = options.TTL_DESCRIPTOR

#: "time for records in logs
LOG_TIME = options.LOG_TIME

#: admin task service address ()
ADMIN_TASKS_SERVER_ORIGIN = options.ADMIN_TASKS_SERVER_ORIGIN

#: request timeout to other services
REQUEST_TIMEOUT = options.REQUEST_TIMEOUT
#: connection timeout to other services
CONNECT_TIMEOUT = options.CONNECT_TIMEOUT

#: request timeout to luna-admin service
ADMIN_REQUEST_TIMEOUT = options.ADMIN_REQUEST_TIMEOUT
#: connection timeout to luna-admin service
ADMIN_CONNECT_TIMEOUT = options.ADMIN_CONNECT_TIMEOUT

#: descriptor count in a re-extract batch
BATCH_SIZE = 8
#: descriptor descriptor for one reextract iteration
MAX_DESCRIPTOR_COUNT_ONE_REEXTRACT_ITERATION = 1000

#: application name
APP_NAME = options.APP_NAME