import tornado
from tornado import web

from configs import config

from app.handlers.image_handler import ImageHandler
from app.handlers.images_handler import ImagesHandler
from app.handlers.buckets_handler import BucketsHandler
from app.handlers.bucket_handler import BucketHandler
from app.handlers.object_handler import ObjectHandler
from app.handlers.objects_handler import ObjectsHandler
from app.handlers.error_handler import ErrorHandler404
from crutches_on_wheels.utils import rid
from crutches_on_wheels.utils.regexps import UUID4_REGEXP_STR
from storage.aws_s3 import s3
from storage import aerospike_cache
from app.handlers.version_handler import VersionHandler
from app.version import VERSION
from configs.config import LOG_TIME, LOG_LEVEL, FOLDER_WITH_LOGS, APP_NAME
from crutches_on_wheels.utils.log import Logger


Logger.initiate(appName=APP_NAME, logLevel=LOG_LEVEL, logTime=LOG_TIME, folderForLog=FOLDER_WITH_LOGS)
logger = Logger()  # : logger for debug printing, in standard mode

API_VERSION = VERSION["Version"]["api"]


BUCKET_REGEXP = "[a-z0-9-_]+"

application = tornado.web.Application([

    (r"/{}/buckets/(?P<bucketName>{})/images/(?P<imageId>{})(?P<thumbnail>_[0-9]+)?".format(API_VERSION, BUCKET_REGEXP,
                                                                                            UUID4_REGEXP_STR),
     ImageHandler),
    (r"/{}/buckets/(?P<bucketName>{})/images".format(API_VERSION, BUCKET_REGEXP),
     ImagesHandler),
    (r"/{}/buckets/(?P<bucketName>{})/objects/(?P<objectId>{})?".format(API_VERSION, BUCKET_REGEXP, UUID4_REGEXP_STR),
     ObjectHandler),
    (r"/{}/buckets/(?P<bucketName>{})/objects".format(API_VERSION, BUCKET_REGEXP),
     ObjectsHandler),
    (r"/{}/buckets".format(API_VERSION),
     BucketsHandler),
    (r"/{}/buckets/(?P<bucketName>{})".format(API_VERSION, BUCKET_REGEXP),
     BucketHandler),
    (r"/version", VersionHandler)


], default_handler_class=ErrorHandler404, **{})

s3.S3.initS3Module(config.S3_HOST, config.S3_AWS_PUBLIC_ACCESS_KEY, config.S3_AWS_SECRET_ACCESS_KEY,
                   config.S3_REGION, config.S3_AUTHORIZATION_SIGNATURE)

rid.setLocalTime(False)

if config.CACHE_ENABLED:
    aerospike_cache.AerospikeCache.initModule(
        aerospike_cache.parseHosts(config.AEROSPIKE_HOSTS), namespace=config.AEROSPIKE_NAMESPACE
)
