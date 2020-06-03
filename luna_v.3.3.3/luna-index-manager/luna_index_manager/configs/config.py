"""Module for parsing config file

Module parse config file and set values in global variables.

Attributes:
    LOG_LEVEL (str): level of debug printing, by priority: ERROR, WARNING, INFO, DEBUG.
    FOLDER_WITH_LOGS (str): folder, where logs are saved. Relative path begin in directory with application.
"""
import sys
import tornado.options
from tornado.options import define, options
from configs.comand_line_args_parser import getOptionsParser
import os


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

    If run sphinx, db_create, db_migrate set python path to root app.
    """
    if sys.argv[0].find("sphinx") > 0 or sys.argv[0].find("db_create") > 0 or sys.argv[0].find("db_migrate") > 0:
        setPythonPathToAPP()


replacePythonPathIfNeed()

define("LOG_LEVEL", default="INFO", help="log level")
define("LOG_TIME", default="UTC", help='time in logs: "LOCAL" or "UTC"')
define("FOLDER_WITH_LOGS", default="./", help="Folder with logs")

define("DB", default="postgres", help="type of database: postgres, oracle, default postgres")
define("DB_USER_NAME", default="luna", help="login to database")
define("DB_PASSWORD", default="luna", help="password to database")
define("DB_NAME", default="luna_index_manager", help="name of database for postgres, sid name for oracle")
define("DB_HOST", default="127.0.0.1", help="ip-address of database")
define("DB_PORT", default=5432, help="database listener port, 5432 - default port of postgres, 1521 - default port of "
                                     "oracle")

define("LUNA_FACES_ORIGIN", default="http://127.0.0.1:5030", help="protocol to LUNA Faces")
define("LUNA_FACES_API_VERSION", default=1, help="api of LUNA Faces")

define("LUNA_CORE_ORIGIN", default="http://127.0.0.1:8083", help="protocol to LUNA Core")
define("LUNA_CORE_API_VERSION", default=14, help="api of LUNA Core")

define("LUNA_MATCHER_DAEMONS", default=["http://127.0.0.1:6000/1"], help="list of luna-matcher-daemon endpoints")

define("MIN_FACES_IN_LIST_FOR_INDEXING", default=50000, help="min face count in list for indexing")
define("INDEXED_FACES_LISTS", default=[], help="lists for indexation, for value ['all'] will be indexed all lists with "
                                               "attributes count > MIN_FACES_IN_LIST_FOR_INDEXING")
define("REQUEST_TIMEOUT", default=60, help="timeout for http-request to external services (LUNA-Faces, LUNA-Core, daemon-matchers)")
define("CONNECT_TIMEOUT", default=30, help="timeout for connect to external services (LUNA-Faces, LUNA-Core, daemon-matchers)")

cmdOptions = getOptionsParser()

tornado.options.parse_config_file(cmdOptions["config"])

DB = options.DB  #: type of database: postgres, oracle, default postgres
DB_USER_NAME = options.DB_USER_NAME  #: login to database
DB_PASSWORD = options.DB_PASSWORD  #: password to database
DB_NAME = options.DB_NAME  #: name of database for postgres, sid name for oracle
DB_HOST = options.DB_HOST  #: ip-address of database
DB_PORT = options.DB_PORT  #: database listener port, 5432 - default port of postgres,
# 1521 - default port of oracle


LUNA_FACES_ORIGIN = options.LUNA_FACES_ORIGIN   #: LUNA Faces origin
LUNA_FACES_API_VERSION = options.LUNA_FACES_API_VERSION  #: LUNA Faces Store api version

LUNA_CORE_ORIGIN = options.LUNA_CORE_ORIGIN   #: protocol to LUNA Core
LUNA_CORE_API_VERSION = options.LUNA_CORE_API_VERSION  #: api of LUNA Faces Core

LUNA_MATCHER_DAEMONS = options.LUNA_MATCHER_DAEMONS     #: list of luna-matcher-daemon endpoint


MIN_FACES_IN_LIST_FOR_INDEXING = options.MIN_FACES_IN_LIST_FOR_INDEXING  #: min face count in list for indexing
INDEXED_FACES_LISTS = options.INDEXED_FACES_LISTS  #: lists for indexation

if DB == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(DB_USER_NAME, DB_PASSWORD, DB_HOST, DB_PORT,
                                                                   DB_NAME)  #: postgresql address
elif DB == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(DB_USER_NAME, DB_PASSWORD, DB_HOST, DB_PORT,
                                                                         DB_NAME)  #: oracle address
else:
    raise ValueError("Bad DB name: {}, supports: postgres or oracle".format(DB))

LOG_LEVEL = options.LOG_LEVEL
LOG_TIME = options.LOG_TIME  # time in logs: "LOCAL" or "UTC"
FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS
CRAWLER_PERIOD = 1 #: crawler period, minutes
APP_NAME = 'luna-index-mngr'  #: application name
REQUEST_TIMEOUT = options.REQUEST_TIMEOUT  #: timeout for http-request to external services (LUNA-Faces, LUNA-Core, daemon-matchers)
CONNECT_TIMEOUT = options.CONNECT_TIMEOUT  #: timeout for connect to external services (LUNA-Faces, LUNA-Core, daemon-matchers)
