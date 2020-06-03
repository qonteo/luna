# -*- coding: utf-8 -*-
"""@package Check Connections

    Module realize check connection functions to internal services (luna-faces, database(specified in config) of api,
    luna-core broker, luna-image-store with portraits)
"""
from luna3.image_store.image_store import StoreApi
from sqlalchemy import create_engine
from sqlalchemy.orm import Query
from app.admin_db import models_admin
from app.api_db import models
from common.api_clients import FACES_CLIENT, CORE_CLIENT, STORE_PORTRAITS_CLIENT, STORE_WARPS_CLIENT
from configs.config import LUNA_API_DB_URI, SQLALCHEMY_DATABASE_URI, ADMIN_DB_TYPE, LUNA_API_DB_TYPE, \
    LUNA_IMAGE_STORE_PORTRAITS_BUCKET, SEND_TO_LUNA_IMAGE_STORE
from app.handlers.app import logger


def checkConnectionToLIS() -> bool:
    """
    Function for check of connection to luna-image-store with portraits. Checks connection itself.
    Data for connection is taken from config.py. If flag SEND_TO_LUNA_IMAGE_STORE is set to 0, no check is done.

    Returns:
        True, if check was passed successfully, else False.
    """
    if not SEND_TO_LUNA_IMAGE_STORE:
        return True

    def checkConnection(client: StoreApi, LISType, bucket):

        logger.debug("Check connection to luna-image-store {}".format(LISType))

        status = client.testConnection(asyncRequest=False)
        if not status:
            logger.error("Check connection to luna-image-store {} is failed".format(LISType))
            return False
        buckets = client.getBuckets(asyncRequest=False, raiseError=True).json
        if bucket not in buckets:
            logger.error("Bucket {} not found in luna-image-store {}".format(bucket, LISType))
            return False
        logger.debug("Connection to luna-image-store {}: OK".format(LISType))
        return True

    return checkConnection(STORE_PORTRAITS_CLIENT, "portraits", LUNA_IMAGE_STORE_PORTRAITS_BUCKET) and \
           checkConnection(STORE_WARPS_CLIENT, "warps", LUNA_IMAGE_STORE_PORTRAITS_BUCKET)


def checkConnectionToDatabase() -> bool:
    """
    Function for check of connection to DB Luna_python_server. Connection and table availability are checked.
    Uri of base is taken from config.py

    Returns:
         True, if check was passed successfully, else False.
    """
    try:
        logger.debug("Check connection to luna-api db")
        if LUNA_API_DB_TYPE == 'postgres':
            engine = create_engine(LUNA_API_DB_URI, connect_args={"connect_timeout": 5})
        else:
            engine = create_engine(LUNA_API_DB_URI)
        with engine.begin() as connection:
            query = Query(models.Account)
            connection.execute(query.statement).cursor.fetchall()
            logger.debug("Connection to luna-api db: OK")
            return True

    except Exception as e:
        logger.exception(e)
        logger.error("EXEPTION checkConnectionToDatabase: " + str(e))
        return False


def checkConnectionToAdminDB() -> bool:
    """
    Function for check of connection to DB luna-admin. Connection and table availability are checked.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully, else False.
    """
    try:
        logger.debug("Check connection to admin db")
        if ADMIN_DB_TYPE == 'postgres':
            engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 5})
        else:
            engine = create_engine(SQLALCHEMY_DATABASE_URI)
        with engine.begin() as connection:
            query = Query(models_admin.Admin)
            res = connection.execute(query.statement).cursor.fetchall()
            if len(res) > 0:
                logger.debug("Connection to admin db: OK")
                return True
            logger.debug("Fail, admin account not found")
            return False

    except Exception as e:
        logger.error(e)
        logger.error("EXEPTION checkConnectionToDatabase: " + str(e))
        return False


def checkConnectionToBroker() -> bool:
    """
    Check connection to luna-core broker.

    Returns:
        True, if check was passed successfully, else False.
    """

    logger.debug("Check connection to broker")
    status = CORE_CLIENT.testConnection(asyncRequest=False)
    if not status:
        logger.error("Check connection to broker is failed")
        return False
    logger.debug("Connection to broker: OK")
    return True


def checkConnectionToFaces() -> bool:
    """
    Check connection to luna-faces broker.

    Returns:
        True, if check was passed successfully, else False.
    """

    logger.debug("Check connection to luna-faces")
    status = FACES_CLIENT.testConnection(asyncRequest=False)
    if not status:
        logger.error("Check connection to luna-faces is failed")
        return False
    logger.debug("Connection to luna-faces: OK")
    return True


def checkConnections() -> bool:
    """
    Functions check connections to luna-faces, api db, admin db,  broker, image store and luna-faces.

    Returns:
        True, if check was passed successfully, else False.
    """
    return checkConnectionToDatabase() and checkConnectionToLIS() and checkConnectionToBroker() \
           and checkConnectionToAdminDB() and checkConnectionToFaces()
