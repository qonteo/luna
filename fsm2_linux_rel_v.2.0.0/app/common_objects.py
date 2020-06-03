from lunavl.httpclient import LunaHttpClient
from common.elasticsearch.elasticsearch import Elasticsearch
from common.timer import Timer
from configs.config import FOLDER_WITH_LOGS, LOG_LEVEL
from configs import config
import sys, logbook, os
from logbook import Logger, StreamHandler
from version import VERSION
from luna3.client import Client

StreamHandler(sys.stdout).push_application()

logbook.set_datetime_format('local')
logger = Logger('FSM2_EVENTS')  # : logger for debug printing, in standard mode
#  "ERROR" is used.  Print is done in standard stream. Can be seen in linux in journalctl, use
# "http://pythonhosted.org/Logbook/index.html"
if LOG_LEVEL == "ERROR":
    logger.level = logbook.ERROR

if LOG_LEVEL == "INFO":
    logger.level = logbook.INFO

if LOG_LEVEL == "DEBUG":
    logger.level = logbook.DEBUG

if LOG_LEVEL == "WARNING":
    logger.level = logbook.WARNING

if FOLDER_WITH_LOGS is None:
    FOLDER_WITH_LOGS = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)) + "/../"

logger.handlers.append(logbook.FileHandler(FOLDER_WITH_LOGS + "/FaceStreamManager2_EVENTS_DEBUG.txt",
                                           level = 'DEBUG', bubble = True))

logger.handlers.append(logbook.FileHandler(FOLDER_WITH_LOGS + "/FaceStreamManager2_EVENTS_ERROR.txt",
                                           level = 'ERROR', bubble = True))

LUNA_CLIENT = LunaHttpClient(api = config.LUNA_API_API_VERSION, endPoint = config.LUNA_API_HOST,
                             port = config.LUNA_API_PORT, token = config.LUNA_API_TOKEN, async = True)

ES_CLIENT = Elasticsearch(logger = logger)

timer = Timer(logger = logger)
LUNA3_CLIENT = Client()
LUNA3_CLIENT.updateLunaCoreSettings(config.LUNA_CORE_HOST, config.LUNA_CORE_PORT, config.LUNA_CORE_PROTOCOL,
                                    config.LUNA_CORE_API_VERSION, True)
LUNA3_CLIENT.updateLunaImageStoreSettings(config.LUNA_IMAGE_STORE_HOST, config.LUNA_IMAGE_STORE_PORT,
                                          config.LUNA_IMAGE_STORE_PROTOCOL, config.LUNA_IMAGE_STORE_API_VERSION, True)
API_VERSION = VERSION['Version']['api']
