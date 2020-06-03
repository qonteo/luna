# -*- coding: utf-8 -*-
"""Check Connections

    Module is used for check of connection with outer services, that use the server.
    At this step we check connection with required tables from config in DB.
"""

from configs.config import SQLALCHEMY_DATABASE_URI, APP_NAME, LOG_LEVEL, STORAGE_TIME, FOLDER_WITH_LOGS
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector
from db.models import Base
from app.handlers.app import logger


def checkConnectionToDatabase():
    """
    Function for check of connection to DB Luna_faces. Connection and tables availability are checked.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully, else False.
    """
    try:
        logger.debug("Check connection to db")
        if 'oracle' in SQLALCHEMY_DATABASE_URI:
            engine = create_engine(SQLALCHEMY_DATABASE_URI)
        else:
            engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args = {"connect_timeout": 5})
        modelsList = [table.__tablename__ for table in Base.__subclasses__()]
        with engine.begin():
            inspector = Inspector.from_engine(engine)
            tableNames = inspector.get_table_names()
            for modelName in modelsList:
                if modelName not in tableNames:
                    logger.debug("Connection to \"{}\" model: FAIL".format(modelName))
                    return False
        logger.debug("Connection to Database check success")
        return True

    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToDatabase: " + str(e))
        return False


def checkConnections():
    """
    Function calls check of all available connections.

    Returns:
        True, if check was passed successfully, else False.
    """
    return checkConnectionToDatabase()
