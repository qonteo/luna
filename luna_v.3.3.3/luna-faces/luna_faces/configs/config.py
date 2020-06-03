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

define("DB", default="postgres", help="type of database: postgres, oracle, default postgres")
define("USER_NAME", default="luna", help="login to database")
define("PASSWORD_DB", default="luna", help="password to database")
define("DB_NAME", default="luna_faces", help="name of database for postgres, sid name for oracle")
define("DB_HOST", default="127.0.0.1", help="ip-address of database")
define("DB_PORT", default=5432, help="database listener port, 5432 - default port of postgres, 1521 - default port of "
                                     "oracle")

define("STORAGE_TIME", default="LOCAL", help="time in which records are stored in the database: LOCAL or UTC")
define("LOG_LEVEL", default="INFO", help="log level")
define("FOLDER_WITH_LOGS", default="./", help="Folder with logs")

cmdOptions = getOptionsParser()

tornado.options.parse_config_file(cmdOptions["config"])

DB = options.DB  #: type of database: postgres, oracle, default postgres
USER_NAME = options.USER_NAME  #: login to database
PASSWORD_DB = options.PASSWORD_DB  #: password to database
DB_NAME = options.DB_NAME  #: name of database for postgres, sid name for oracle
DB_HOST = options.DB_HOST  #: ip-address of database
DB_PORT = options.DB_PORT  #: database listener port, 5432 - default port of postgres,
# 1521 - default port of oracle

if DB == "postgres":
    SQLALCHEMY_DATABASE_URI = 'postgresql://{}:{}@{}:{}/{}'.format(USER_NAME, PASSWORD_DB, DB_HOST, DB_PORT,
                                                                   DB_NAME)  #: postgresql address
elif DB == "oracle":
    SQLALCHEMY_DATABASE_URI = 'oracle+cx_oracle://{}:{}@{}:{}/{}'.format(USER_NAME, PASSWORD_DB, DB_HOST, DB_PORT,
                                                                         DB_NAME)  #: oracle address
else:
    raise ValueError("Bad DB name: {}, supports: postgres or oracle".format(DB))

LOG_LEVEL = options.LOG_LEVEL  #: level of debug printing, by priority: ERROR, WARNING, INFO, DEBUG
STORAGE_TIME = options.STORAGE_TIME  #: time for records in logs
FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS  #: folder to save logs
APP_NAME = "luna-faces"                      #: application name
