# -*- coding: utf-8 -*-
"""Check Connections

    Module is used for check of connection with outer services, that use the server.
    At this step we check connection with LUNA brokers, availability of required bucket in luna-image-store and availability
    of required table from config in DB.
"""

from configs.config import SQLALCHEMY_DATABASE_URI, USE_INDEX_MANAGER, DB
from configs.config import SEND_TO_LUNA_IMAGE_STORE, LUNA_IMAGE_STORE_BUCKET
from app.common import logger, luna3Client
from sqlalchemy import create_engine
from sqlalchemy.orm import Query
from db import models


def checkConnectionToLIS() -> bool:
    """
    Function for check of connection to luna-image-store. Checks connection itself.
    Data for connection is taken from config.py. If flag SEND_TO_LUNA_IMAGE_STORE is set to 0, no check is done.

    Returns:
        True, if check was passed successfully, else False.
    """
    if not SEND_TO_LUNA_IMAGE_STORE:
        return True
    try:
        logger.debug("Check connection to luna-image-store")
        connectionStatus = luna3Client.lunaImageStore.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Version luna image store api does not match with given")
            return False
        buckets = luna3Client.lunaImageStore.getBuckets(asyncRequest=False).json
        if LUNA_IMAGE_STORE_BUCKET not in buckets:
            logger.error("Bucket {} not found in luna-image-store".format(LUNA_IMAGE_STORE_BUCKET))
            return False
        logger.debug("Connection to luna-image-store: OK")
        return True
    except Exception:
        logger.exception("EXEPTION checkConnectionToLIS")
        return False


def checkConnectionToLunaFaces() -> bool:
    """
    Function to check connection to luna-faces. Checks connection itself.
    Data for connection is taken from config.py.

    Returns:
        True, if check was passed successfully, else False.
       """
    try:
        logger.debug("Check connection to luna-faces")
        connectionStatus = luna3Client.lunaFaces.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Version luna-faces api does not match with given")
            return False
        logger.debug("Connection to luna-faces: OK")
        return True
    except Exception:
        logger.exception("EXEPTION checkConnectionToLunaFaces")
        return False


def checkConnectionToDatabase() -> bool:
    """
    Function for check of connection to DB Luna_python_server. Connection and table availability are checked.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully, else False.
    """
    try:
        logger.debug("Check connection to db")
        if DB == 'postgres':
            engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 5})
        else:
            # analogue of connect_timeout for oracle not found or not exists
            engine = create_engine(SQLALCHEMY_DATABASE_URI)
        with engine.begin() as connection:
            query = Query(models.Account)
            connection.execute(query.statement).cursor.fetchall()
            logger.debug("Connection to db: OK")
            return True

    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToDatabase: " + str(e))
        return False


def checkConnectionToBroker() -> bool:
    """
    Function for check connection with LUNA broker. Requests LUNA version.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully (200 code is returned), else False.
    """
    try:
        connectionStatus = luna3Client.lunaCore.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Luna core version does not match with version in config")
            return False
        logger.debug("Connection to Luna Core: OK")
        return True
    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToBroker: " + str(e))
        return False


def checkConnectionToIndexManager() -> bool:
    """
    Function for check connection to LUNA Index Manager. Requests LUNA Index Manager version.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully (200 code is returned), else False.
    """
    if not USE_INDEX_MANAGER:
        return True
    try:
        connectionStatus = luna3Client.lunaIndexManager.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Luna Index Manager version does not match with version in config")
            return False
        logger.debug("Connection to Luna Index Manager: OK")
        return True
    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToIndexManager: " + str(e))
        return False


def checkConnections() -> bool:
    """
    Function calls check of all available connections.

    Returns:
        True, if check was passed successfully, else False.
    """
    return checkConnectionToBroker() and checkConnectionToDatabase() and checkConnectionToLIS() and \
           checkConnectionToLunaFaces() and checkConnectionToIndexManager()
