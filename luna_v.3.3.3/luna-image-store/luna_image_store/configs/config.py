import os
import sys

import tornado
from tornado.options import define, options

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

    If run sphinx, db_create, influx_db_create, s3_bucket_create, db_migrate set python path to root app.
    """
    if sys.argv[0].find("sphinx") > 0 or sys.argv[0].find("db_create") > 0 or sys.argv[0].find("influx_db_create") \
            or sys.argv[0].find("s3_bucket_create") > 0 or sys.argv[0].find("db_migrate"):
        setPythonPathToAPP()


replacePythonPathIfNeed()

define("STORAGE_TYPE", default="LOCAL", help="`LOCAL` or `S3`")

define("S3_HOST", default="http://localhost:7480", help="S3 host")
define("S3_REGION", default="", help="S3 region")
define("S3_AWS_PUBLIC_ACCESS_KEY", help="S3 public access key")
define("S3_AWS_SECRET_ACCESS_KEY", help="S3 secret access key")
define("S3_AUTHORIZATION_SIGNATURE", default="s3v4", help='version of authorization signature ("s3v2" or "s3v4")')

define("LOCAL_STORAGE", default="./local_storage", help="directory for images storing")

define("CACHE_ENABLED", default=False, help="Enable cache for store objects in fast storage")
define("MAX_CACHEABLE_SIZE", default=1000000, help="Max size for caching objects. In bytes.")
define("AEROSPIKE_HOSTS", default=["127.0.0.1:3000"], help="aerospike hosts", multiple=True)
define("AEROSPIKE_NAMESPACE", default='luna_temporary', help="aerospike namespace for use as cache")

define("LOG_TIME", default="LOCAL", help="time for records in logs: LOCAL or UTC")
define("LOG_LEVEL", default="INFO", help="log level")
define("FOLDER_WITH_LOGS", default="./", help="Folder with logs")

cmdOptions = getOptionsParser()

tornado.options.parse_config_file(cmdOptions["config"])

S3_HOST = options.S3_HOST  #: endpoint of s3
S3_REGION = options.S3_REGION  #: region of amazon s3
S3_AWS_PUBLIC_ACCESS_KEY = options.S3_AWS_PUBLIC_ACCESS_KEY  #: public *access key* to access s3
S3_AWS_SECRET_ACCESS_KEY = options.S3_AWS_SECRET_ACCESS_KEY  #: private *access key* to access s3
S3_AUTHORIZATION_SIGNATURE = options.S3_AUTHORIZATION_SIGNATURE  #: version of authorization signature

LOG_LEVEL = options.LOG_LEVEL  #: level of debug printing, by priority: ERROR, WARNING, INFO, DEBUG
LOG_TIME = options.LOG_TIME  #: "time for records in logs
FOLDER_WITH_LOGS = options.FOLDER_WITH_LOGS  #: folder to save logs

LOCAL_STORAGE = options.LOCAL_STORAGE  #: directory for images storing

STORAGE_TYPE = options.STORAGE_TYPE  #: repository type for images, `LOCAL` or `S3`

CACHE_ENABLED = options.CACHE_ENABLED  #: Enable cache for store objects in fast storage
MAX_CACHEABLE_SIZE = options.MAX_CACHEABLE_SIZE  #: Max size for caching objects. In bytes.
AEROSPIKE_HOSTS = options.AEROSPIKE_HOSTS  #: aerospike hosts list.
AEROSPIKE_NAMESPACE = options.AEROSPIKE_NAMESPACE #: aerospike default namespace.

REQUEST_TIMEOUT = 60  #: timeout for http-request to external services (LUNA, statistics)
CONNECT_TIMEOUT = 30  #: timeout for connect to external services (LUNA, statistics)

THUMBNAILS = [32, 64, 96, 160]  #: thumbnails size

APP_NAME = "luna-image-store"      #: application name
