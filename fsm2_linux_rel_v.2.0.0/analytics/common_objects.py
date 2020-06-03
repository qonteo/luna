from common.elasticsearch.elasticsearch import Elasticsearch
from configs.config import FOLDER_WITH_LOGS
from configs import config
from common.timer import Timer
from configs.config import LOG_LEVEL
import sys, logbook, os
from logbook import Logger, StreamHandler
from lunavl.httpclient import LunaHttpClient

StreamHandler(sys.stdout).push_application()

logbook.set_datetime_format('local')
logger = Logger('FSM2_ANALYTICS')  # : logger for debug printing, in standard mode
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



timer = Timer(logger=logger)

if FOLDER_WITH_LOGS is None:
    FOLDER_WITH_LOGS = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)) + "/../"

logger.handlers.append(logbook.FileHandler(FOLDER_WITH_LOGS + "/FaceStreamManager2_ANALYTICS_DEBUG.txt",
                                           level = 'DEBUG', bubble = True))

logger.handlers.append(logbook.FileHandler(FOLDER_WITH_LOGS + "/FaceStreamManager2_ANALYTICS_ERROR.txt",
                                           level = 'ERROR', bubble = True))

LUNA_CLIENT = LunaHttpClient(api = config.LUNA_API_API_VERSION, endPoint = config.LUNA_API_HOST,
                             port = config.LUNA_API_PORT, token = config.LUNA_API_TOKEN, async = True)


ES_CLIENT = Elasticsearch(logger = logger)