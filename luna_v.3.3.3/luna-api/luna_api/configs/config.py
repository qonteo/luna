# -*- coding: utf-8 -*-
"""
This file contains configurations for system functioning.
"""
import socket

import tornado.options
from tornado.options import define, options
from configs.comand_line_args_parser import getOptionsParser
import os, sys


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

    If run sphinx, db_create, influx_db_create, lis_bucket_create, db_migrate set python path to root app.
    """
    if sys.argv[0].find("sphinx") > 0 or sys.argv[0].find("db_create") > 0 or sys.argv[0].find("influx_db_create") \
            or sys.argv[0].find("lis_bucket_create") > 0 or sys.argv[0].find("db_migrate"):
        setPythonPathToAPP()


def get_ip_address():
    """
    Function to get server ip-address, where service is launched, need internet for correct work

    :return: IP-address or "127.0.0.1"
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((DNS_SERVER, 80))
        return s.getsockname()[0]
    except Exception:
        print("cannot determinate ip address, using '127.0.0.1")
        return "127.0.0.1"


replacePythonPathIfNeed()


#: installation
if "DB_USER_NAME" not in options:  # crutch for sphinx, sphinx double import this file
    define("DB", default="postgres", help="type of database: postgres, oracle, default postgres")
    define("DB_USER_NAME", default="faceis", help="login to database")
    define("DB_PASSWORD", default="faceis", help="password to database")
    define("DB_NAME", default="faceis_db", help="name of database for postgres, sid name for oracle")
    define("DB_HOST", default="127.0.0.1", help="ip-address of database")
    define("DB_PORT", default=5432, help="database listener port, 5432 - default port of postgres, "
                                                   "1521 - default port of oracle")

    define("LUNA_CORE_ORIGIN", default="http://127.0.0.1:8083", help="LUNA Core origin")
    define("LUNA_CORE_API_VERSION", default=14, help="LUNA Core api version")

    define("USE_INDEX_MANAGER", default=0, help="parameter, which indicates whether to use Index Manager")
    define("LUNA_INDEX_MANAGER_ORIGIN", default="http://127.0.0.1:5060", help="LUNA Index Manager origin")
    define("LUNA_INDEX_MANAGER_API_VERSION", default=1, help="LUNA Index Manager origin")

    define("SEND_TO_LUNA_IMAGE_STORE", default=1, help="save portrait to LUNA Image Store")
    define("LUNA_IMAGE_STORE_ORIGIN", default="http://127.0.0.1:5020", help="LUNA Image Store origin")
    define("LUNA_IMAGE_STORE_API_VERSION", default=1, help="LUNA Image Store api version")
    define("LUNA_IMAGE_STORE_BUCKET", default="portraits", help="LUNA Image Store bucket")

    define("LUNA_FACES_ORIGIN", default="http://127.0.0.1:5030", help="LUNA Faces Store origin")
    define("LUNA_FACES_API_VERSION", default=1, help="LUNA Faces Store api version")

    define("SEND_ADMIN_STATS", default=1, help="send admin stats")
    define("ADMIN_STATISTICS_SERVER_ORIGIN", default="http://127.0.0.1:8086", help="Admin statistic server origin")
    define("ADMIN_STATISTICS_DB", default="luna_api_admin", help="Influx database")

    define("SEND_ACCOUNT_STATS", default=1, help="send account stats")
    define("ACCOUNTS_STATISTICS_SERVER", default="http://127.0.0.1:5009/internal/lps_event",
           help="Account statistic host host")

    define("MAX_CANDIDATE_IN_RESPONSE", default=5, help="max person count in response for match")

    define("LOG_LEVEL", default="DEBUG", help="log level")
    define("LOG_TIME", default="LOCAL", help="time for records in logs: LOCAL or UTC")
    define("FOLDER_WITH_LOGS", default="./", help="Folder with logs")

    define("ENABLE_PLUGINS", default=0, help="enable support of plug-ins")

cmdOptions = getOptionsParser()

tornado.options.parse_config_file(cmdOptions["config"])

#: type of database: oracle or postgres
DB = options.DB
#: database login
DB_USER_NAME = options.DB_USER_NAME
#: database password
DB_PASSWORD = options.DB_PASSWORD
#: database name, where all schemes are created
DB_NAME = options.DB_NAME
#: database ip-address
DB_HOST = options.DB_HOST
#: database listener port
DB_PORT = str(options.DB_PORT)
#: database address
if DB == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER_NAME, DB_PASSWORD, DB_HOST, DB_PORT,
                                                                   DB_NAME)  #: postgresql address
elif DB == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(DB_USER_NAME, DB_PASSWORD, DB_HOST, DB_PORT,
                                                                         DB_NAME)  #: oracle address
else:
    raise ValueError("Bad DB name: {}, supports: postgres or oracle".format(DB))

#: LUNA Core origin
LUNA_CORE_ORIGIN = options.LUNA_CORE_ORIGIN
#: LUNA Core api version
LUNA_CORE_API_VERSION = options.LUNA_CORE_API_VERSION

#: parameter indicates whether to use Luna Index Manager
USE_INDEX_MANAGER = options.USE_INDEX_MANAGER
#: LUNA Index Manager url
LUNA_INDEX_MANAGER_ORIGIN = options.LUNA_INDEX_MANAGER_ORIGIN
#: api of LUNA Index Manager
LUNA_INDEX_MANAGER_API_VERSION = options.LUNA_INDEX_MANAGER_API_VERSION

#: flag, which indicates whether send portraits to LUNA Image Store or not
SEND_TO_LUNA_IMAGE_STORE = options.SEND_TO_LUNA_IMAGE_STORE
#: LUNA Image Store origin
LUNA_IMAGE_STORE_ORIGIN = options.LUNA_IMAGE_STORE_ORIGIN
#: LUNA Image Store api versio
LUNA_IMAGE_STORE_API_VERSION = options.LUNA_IMAGE_STORE_API_VERSION
#: name *bucket*, where portraits will be stored
LUNA_IMAGE_STORE_BUCKET = options.LUNA_IMAGE_STORE_BUCKET

#: LUNA Faces Store origin
LUNA_FACES_ORIGIN = options.LUNA_FACES_ORIGIN
#: LUNA Faces Store api version
LUNA_FACES_API_VERSION = options.LUNA_FACES_API_VERSION

#: parameter, which indicates whether to send admin statistics or not
SEND_ADMIN_STATS = options.SEND_ADMIN_STATS
#: influxdb server to collect statistics
ADMIN_STATISTICS_SERVER_ORIGIN = options.ADMIN_STATISTICS_SERVER_ORIGIN
#: database name of influxdb
ADMIN_STATISTICS_DB = options.ADMIN_STATISTICS_DB

#: parameter, which indicates whether tj send client statistics or not
SEND_ACCOUNT_STATS = options.SEND_ACCOUNT_STATS
#: client address to send statistics
ACCOUNTS_STATISTICS_SERVER = options.ACCOUNTS_STATISTICS_SERVER

#: maximum number of candidates in matching response
MAX_CANDIDATE_IN_RESPONSE = options.MAX_CANDIDATE_IN_RESPONSE

#: level of debug printing, by priority: ERROR, WARNING, INFO, DEBUG
LOG_LEVEL = options.LOG_LEVEL
#: "time for records in logs
LOG_TIME = options.LOG_TIME
#: folder to save logs
FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS

#: enable plug-ins
ENABLE_PLUGINS = options.ENABLE_PLUGINS

#: timeout for http-request to external services (LUNA, statistics)
REQUEST_TIMEOUT = 60
#: timeout for connect to external services (LUNA, statistics)
CONNECT_TIMEOUT = 20

#: value of header "Access-Control-Allow-Origin"
ACCESS_CONTROL_ALLOW_ORIGIN = "*"

#: dns-server for detection ip address of the machine, by default using google dns server (need connection to internet)
DNS_SERVER = "8.8.8.8"

#: ip-address of the server, you can this parameter manually
SERVER_IP = get_ip_address()

#: time delta in seconds to store list of indexed lists in cache
CHECK_INDEX_DELTA = 60
APP_NAME = "luna-api"                               #: application mame