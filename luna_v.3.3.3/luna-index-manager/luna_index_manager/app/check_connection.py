"""Check connection.

Check connection to all external services.
"""
import requests
from luna3.core.core import CoreAPI
from luna3.faces.faces import FacesApi

from app.app import logger
from configs.config import LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, LUNA_CORE_ORIGIN, LUNA_CORE_API_VERSION, \
    LUNA_MATCHER_DAEMONS, SQLALCHEMY_DATABASE_URI, CONNECT_TIMEOUT, REQUEST_TIMEOUT
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector

from db.models import Base


def checkConnectionToDatabase() -> bool:
    """
    Function for check of connection to DB Luna_faces. Connection and tables availability are checked.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully, else False.
    """
    try:
        logger.info("Check connection to db")
        if 'oracle' in SQLALCHEMY_DATABASE_URI:
            engine = create_engine(SQLALCHEMY_DATABASE_URI)
        else:
            engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 5})
        modelsList = [table.__tablename__ for table in Base.__subclasses__()]
        with engine.begin():
            inspector = Inspector.from_engine(engine)
            tableNames = inspector.get_table_names()
            for modelName in modelsList:
                if modelName not in tableNames:
                    logger.error("Table \"{}\" not found".format(modelName))
                    return False
        logger.info("Connection to Database check success")
        return True

    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToDatabase: " + str(e))
        return False


def checkConnectionToFaces() -> bool:
    """
    Function to check connection to luna-faces. Checks connection itself.
    Data for connection is taken from config.py.

    Returns:
        True, if check was passed successfully, else False.
       """
    try:
        facesClient = FacesApi(LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, asyncRequest=True,
                               connectTimeout=CONNECT_TIMEOUT, requestTimeout=REQUEST_TIMEOUT)
        logger.info("Check connection to luna-faces")
        connectionStatus = facesClient.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Version luna-faces api does not match with given")
            return False
        logger.info("Connection to luna-faces: OK")
        return True
    except Exception:
        logger.exception("EXEPTION checkConnectionToLunaFaces")
        return False


def checkConnectionToBroker() -> bool:
    """
    Function for check connection with LUNA broker. Requests LUNA version.
    Uri of base is taken from config.py

    Returns:
        True, if check was passed successfully (200 code is returned), else False.
    """
    try:
        logger.info("Check connection to luna-broker")
        coreClient = CoreAPI(origin=LUNA_CORE_ORIGIN, api=LUNA_CORE_API_VERSION, asyncRequest=False,
                             connectTimeout=CONNECT_TIMEOUT, requestTimeout=REQUEST_TIMEOUT)
        connectionStatus = coreClient.testConnection(asyncRequest=False)
        if not connectionStatus:
            logger.error("Luna core version does not match with version in config")
            return False
        logger.info("Connection to luna-broker: OK")
        return True
    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToBroker: " + str(e))
        return False


def checkConnectionToMatcherDaemons() -> bool:
    """
    Function for check connection to LUNA Matcher Daemons. Requests LUNA Matcher Daemons version.
    Urls are taken from config.py

    Returns:
        True, if check was passed successfully (200 code is returned), else False.
    """
    try:
        logger.info("Check connection to luna-matcher-daemons")
        for daemonUrl in LUNA_MATCHER_DAEMONS:
            url = "{}/uploaded_generations".format(daemonUrl)
            reply = requests.get(url, timeout=REQUEST_TIMEOUT)
            connectionStatus = reply.status_code == 200
            if not connectionStatus:
                logger.error(
                    'Luna luna-matcher-daemon "{}" version does not match with version in config'.format(daemonUrl))
                return False
        logger.info("Connection to luna-matcher-daemons: OK")
        return True
    except Exception as e:
        logger.exception()
        logger.error("EXEPTION checkConnectionToBroker: " + str(e))
        return False


def checkConnections():
    return checkConnectionToDatabase() and checkConnectionToBroker() and checkConnectionToFaces() and \
           checkConnectionToMatcherDaemons()
