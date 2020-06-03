from luna3.client import Client
from typing import Optional

from configs.config import ENABLE_PLUGINS, APP_NAME, LOG_LEVEL, LOG_TIME, FOLDER_WITH_LOGS
from configs.config import LUNA_CORE_ORIGIN, LUNA_CORE_API_VERSION, LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION
from configs.config import LUNA_IMAGE_STORE_ORIGIN, LUNA_IMAGE_STORE_API_VERSION
from configs.config import LUNA_INDEX_MANAGER_ORIGIN, LUNA_INDEX_MANAGER_API_VERSION
from configs.config import REQUEST_TIMEOUT, CONNECT_TIMEOUT
from app.plugin_manager import loadPlugins
from crutches_on_wheels.utils import rid
from crutches_on_wheels.utils.log import Logger


def generateLuna3Client(requestId: Optional[str] = None) -> Client:
    """
    Generate luna3 client
    Args:
        requestId: request id

    Returns:
        luna3 client
    """
    client = Client(requestId)
    client.updateLunaFacesSettings(origin=LUNA_FACES_ORIGIN, api=LUNA_FACES_API_VERSION, asyncRequest=True,
                                        requestTimeout=REQUEST_TIMEOUT, connectTimeout=CONNECT_TIMEOUT)
    client.updateLunaImageStoreSettings(origin=LUNA_IMAGE_STORE_ORIGIN, api=LUNA_IMAGE_STORE_API_VERSION,
                                             asyncRequest=True, requestTimeout=REQUEST_TIMEOUT,
                                             connectTimeout=CONNECT_TIMEOUT)
    client.updateLunaCoreSettings(origin=LUNA_CORE_ORIGIN, api=LUNA_CORE_API_VERSION, asyncRequest=True,
                                       requestTimeout=REQUEST_TIMEOUT, connectTimeout=CONNECT_TIMEOUT)
    client.updateLunaIndexManagerSettings(origin=LUNA_INDEX_MANAGER_ORIGIN, api=LUNA_INDEX_MANAGER_API_VERSION,
                                               asyncRequest=True, requestTimeout=REQUEST_TIMEOUT,
                                               connectTimeout=CONNECT_TIMEOUT)
    return client


luna3Client = generateLuna3Client()

Logger.initiate(APP_NAME, LOG_LEVEL, LOG_TIME, FOLDER_WITH_LOGS)
logger = Logger()  # : logger for debug printing, in standard mode

rid.setLocalTime(False)

SETTER_PORTRAITS_PLUGINS = []
GETTER_PORTRAITS_PLUGINS = []
ADMIN_STATISTICS_PLUGINS = []
ACCOUNT_STATISTICS_PLUGINS = []

if ENABLE_PLUGINS:
    from app.plugin_manager import SETTER_PORTRAITS_PLUGINS, GETTER_PORTRAITS_PLUGINS, \
        ADMIN_STATISTICS_PLUGINS, ACCOUNT_STATISTICS_PLUGINS
else:
    pass
