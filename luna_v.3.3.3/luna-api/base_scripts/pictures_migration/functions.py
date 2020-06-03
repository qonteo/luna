from luna3.client import Client
from tornado.options import parse_config_file, options, define
from tornado.options import OptionParser
import logbook
from typing import Tuple
import os, sys
import asyncio

logger = logbook.Logger('pictures migration')
logger.level = logbook.DEBUG
logbook.StreamHandler(sys.stdout).push_application()
logger.handlers.append(logbook.FileHandler("./pictures_migration_DEBUG.log", level='DEBUG', bubble=True))
logger.handlers.append(logbook.FileHandler("./pictures_migration_ERROR.log", level='ERROR', bubble=True))


def getCmdParser():
    """
    Get the start option.

    note: In command line you can set *config, image_path*.
    *config* - config location
    *image_path* - path where luna-api stores images

    Returns:
        parsed options
    """
    op = OptionParser()
    op.define('config', default="./config.conf", help='config location')
    op.parse_command_line()
    return op


def initConfig() -> Tuple[str, int, str, str]:
    """
    Config initialization from config.conf

    Returns:
        image store origin, api version and bucket
    """
    define("LUNA_IMAGE_STORE_ORIGIN", default="http://127.0.0.1:5020", help="LUNA Image Store origin")
    define("LUNA_IMAGE_STORE_API_VERSION", type=int, default=1, help="LUNA Image Store api version")
    define("LUNA_IMAGE_STORE_BUCKET", default="visionlabs-samples", help="LUNA Image Store bucket for samples")

    define("IMAGE_PATH", default="../../luna_api/portraits", help="portraits location")
    define("WORKERS_COUNT", default=1, help="workers count")

    cmdOptions = getCmdParser()
    parse_config_file(cmdOptions['config'])

    return options.LUNA_IMAGE_STORE_ORIGIN, options.LUNA_IMAGE_STORE_API_VERSION, \
           options.LUNA_IMAGE_STORE_BUCKET, options.IMAGE_PATH, options.WORKERS_COUNT


LIS_ORIGIN, LIS_API_VERSION, LIS_BUCKET, IMAGE_PATH, WORKERS_COUNT = initConfig()
luna3Client = Client()
luna3Client.updateLunaImageStoreSettings(LIS_ORIGIN, LIS_API_VERSION, asyncRequest=True)


def checkConnection() -> bool:
    """
    Function for check of connection to luna-image-store. Checks connection itself.

    Returns:
        True, if check was passed successfully, else False.
    """
    try:
        logger.debug("Check connection to luna-image-store")
        connectionStatus = luna3Client.lunaImageStore.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Version luna image store api does not match with given")
            return False
        buckets = luna3Client.lunaImageStore.getBuckets(asyncRequest=False).json
        if LIS_BUCKET not in buckets:
            logger.error("Bucket {} not found in luna-image-store".format(LIS_BUCKET))
            return False
        logger.debug("Connection to luna-image-store: OK")
        return True
    except Exception:
        logger.exception("EXEPTION checkConnectionToLIS")
        return False


async def migratePictures() -> Tuple[int, int]:
    """
    Migrate picrutes from luna-api to luna-image-store

    Returns:
        succeess and error images' migration count
    """
    successCount = errorCount = 0

    async def migratePath(pathIter: iter) -> None:
        """
        Transfer pictures from path
        Args:
            pathIter: path iter
        """
        nonlocal successCount, errorCount
        for subPath in pathIter:
            for imageName in os.listdir(os.path.join(IMAGE_PATH, subPath)):
                with open(os.path.join(IMAGE_PATH, subPath, imageName), 'rb') as imageFile:
                    try:
                        await luna3Client.lunaImageStore.putImage(imageFile.read(), imageName.split('.')[0], LIS_BUCKET,
                                                                  raiseError=True)
                        successCount += 1
                        if not successCount % 100:
                            logger.debug(f'{successCount}  images transfered')
                    except Exception as e:
                        errorCount += 1
                        logger.exception()

    pathIter = iter(os.listdir(IMAGE_PATH))
    await asyncio.gather(*[migratePath(pathIter) for _ in range(WORKERS_COUNT)])

    return successCount, errorCount
