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

    If run sphinx, db_create, influx_db_create, s3_bucket_create, db_migrate set python path to root app.
    """
    if sys.argv[0].find("sphinx") > 0 or sys.argv[0].find("db_create") > 0 or sys.argv[0].find("influx_db_create") \
            or sys.argv[0].find("s3_bucket_create") > 0 or sys.argv[0].find("db_migrate"):
        setPythonPathToAPP()


replacePythonPathIfNeed()

define("LUNA_API_HOST", default="http://localhost", help="LUNA API host")
define("LUNA_API_PORT", default=5000, type=int, help="LUNA API port")
define("LUNA_API_API_VERSION", default=3, type=int, help="LUNA API api Version")
define("LUNA_API_TOKEN", type=str, help="Token for access to LUNA API")

define("LUNA_IMAGE_STORE_HOST", default="http://localhost", help="LUNA IMAGE STORE host")
define("LUNA_IMAGE_STORE_PORT", default=5020, type=int, help="LUNA IMAGE STORE port")
define("LUNA_IMAGE_STORE_API_VERSION", default=1, type=int, help="LUNA IMAGE STORE api Version")
define("LUNA_IMAGE_STORE_WARPS_BUCKET", type=str,
       help="LUNA IMAGE STORE bucket for storing warped images from extractor")

define("LUNA_CORE_HOST", default="http://localhost", help="LUNA CORE host")
define("LUNA_CORE_PORT", default=8083, type=int, help="LUNA CORE port")
define("LUNA_CORE_API_VERSION", default=13, type=int, help="LUNA CORE api Version")

define("ELASTICSEARCH_HOST", default="http://localhost", help="ELASTICSEARCH host")
define("ELASTICSEARCH_PORT", default=9200, type=int, help="ELASTICSEARCH port")

define("ADMIN_STATISTICS_SERVER", default="http://localhost:8086",
       help="Admin statistic host host")

define("LOG_LEVEL", default="DEBUG", help="log level")
define("ADMIN_STATISTICS_DB", default="matching_test", help="Influx database")
define("FOLDER_WITH_LOGS", default=None, help="Folder with logs")
define("USE_LATEX", default=0, help="Shows weather to use latex")
define("SAVE_INPUT_IMAGES", default=0, help="Shows whether to save input images")
define("SEND_ADMIN_STATS", type=int, default=1, help="send admin stats, 0 or 1")
cmdOptions = getOptionsParser()

tornado.options.parse_config_file(cmdOptions["config"])

LUNA_API_HOST = options.LUNA_API_HOST  #: LUNA url
LUNA_API_PORT = options.LUNA_API_PORT  #: LUNA url
LUNA_API_API_VERSION = options.LUNA_API_API_VERSION  #: LUNA url
LUNA_API_TOKEN = options.LUNA_API_TOKEN  #: LUNA Api token

LUNA_CORE_HOST = options.LUNA_CORE_HOST.split("://")[1]  #: LUNA CORE STORE host
LUNA_CORE_PROTOCOL = options.LUNA_CORE_HOST.split("://")[0]  #: LUNA CORE protocol
LUNA_CORE_PORT = options.LUNA_CORE_PORT  #: LUNA CORE port
LUNA_CORE_API_VERSION = options.LUNA_CORE_API_VERSION  #: LUNA CORE api Version

LUNA_IMAGE_STORE_HOST = options.LUNA_IMAGE_STORE_HOST.split("://")[1]  #: LUNA IMAGE STORE host
LUNA_IMAGE_STORE_PROTOCOL = options.LUNA_IMAGE_STORE_HOST.split("://")[0]  #: LUNA IMAGE STORE protocol
LUNA_IMAGE_STORE_PORT = options.LUNA_IMAGE_STORE_PORT  #: LUNA IMAGE STORE port
LUNA_IMAGE_STORE_API_VERSION = options.LUNA_IMAGE_STORE_API_VERSION  #: LUNA IMAGE STORE api Version
LUNA_IMAGE_STORE_WARPS_BUCKET = options.LUNA_IMAGE_STORE_WARPS_BUCKET  #: LUNA IMAGE STORE bucket for storing warped images from extractor

ELASTICSEARCH_URL = "{}:{}".format(options.ELASTICSEARCH_HOST, options.ELASTICSEARCH_PORT)
LOG_LEVEL = options.LOG_LEVEL  #: level of debug printing, by priority: ERROR, WARNING, INFO, DEBUG

ADMIN_STATISTICS_SERVER = options.ADMIN_STATISTICS_SERVER  #: influxdb server to collect statistics
ADMIN_STATISTICS_DB = options.ADMIN_STATISTICS_DB  #: database name of influxdb

FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS  #: folder to save logs
USE_LATEX = options.USE_LATEX
SAVE_INPUT_IMAGES = options.SAVE_INPUT_IMAGES

REQUEST_TIMEOUT = 60  #: timeout for http-request to external services (LUNA, statistics)
CONNECT_TIMEOUT = 20  #: timeout for connect to external services (LUNA, statistics)

GENDER_THRESHOLD = 0.5

SEND_ADMIN_STATS = options.SEND_ADMIN_STATS  #: parameter, which indicates whether send admin statistics or not

MAX_TRY_COUNT = 5

# DO NOT SET GREATER THAN 8*10**6
MAX_OBJECTS_TO_ATTACH = 10 ** 6  #: count of, for example, events, to attach to luna list

CANDIDATES_TO_STORE = 5  #: count of candidates to store from weighted match reply
