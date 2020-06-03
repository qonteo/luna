from datetime import datetime
from sqlalchemy import and_, insert, create_engine, func
from sqlalchemy.orm import Query
from sqlalchemy.engine.reflection import Inspector
from models import oldModels, newModels, baseOld, baseNew, newAccModels, baseAccNew
from tornado.options import parse_config_file, options, define
from tornado.options import OptionParser
from logbook import Logger
from sqlalchemy.exc import IntegrityError
import logbook
import sys

logger = Logger('db-migration')
logger.level = logbook.DEBUG
logbook.StreamHandler(sys.stdout).push_application()
logger.handlers.append(logbook.FileHandler("./db_migration_DEBUG.log", level='DEBUG', bubble=True))
logger.handlers.append(logbook.FileHandler("./db_migration_ERROR.log", level='ERROR', bubble=True))

# person list type in old db
personListType = True
# page size for work with
LIMIT = 1000
# default list create time
LIST_CREATE_TIME = datetime.utcnow()

newTableNames = ('face', 'person', 'list', 'list_face', 'list_person', 'account', 'account_token')
counters = dict(zip(newTableNames, [{'success': 0, 'errors': 0} for _ in range(len(newTableNames))]))


def getCmdParser():
    """
    Get the start option.

    note: In command line you can set two arguments *clean, config*.
    *clean* - flag, if true - remove old tables from db
    *skip_migration* - flag, if true - skip tables migration
    *config* - config location

    Returns:
        parsed options
    """
    op = OptionParser()
    op.define('skip_migration', default=False, help='Enable skip tables migration')
    op.define('clean', default=False, help='Enable/disable drop tables from old database')
    op.define('config', default="./config.conf", help='config location')
    op.define('migrate_accounts', default=True, help='Enable/disable migrate account and accountToken tables')
    op.parse_command_line()
    return op


def initConfig():
    """
    Config initialization from config.conf

    Returns:
        urls of database
    """
    define('OLD_DB_TYPE', default='postgres')
    define('OLD_DB_NAME', default='faceis_db')
    define('OLD_DB_IP', default='127.0.0.1')
    define('OLD_DB_PORT', default='5432')
    define('OLD_DB_USER_NAME', default='faceis')
    define('OLD_DB_PASSWORD', default='faceis')
    define('NEW_DB_TYPE', default='postgres')
    define('NEW_DB_NAME', default='luna_faces')
    define('NEW_DB_IP', default='127.0.0.1')
    define('NEW_DB_PORT', default='5432')
    define('NEW_DB_USER_NAME', default='luna')
    define('NEW_DB_PASSWORD', default='luna')
    define('NEW_ACC_DB_TYPE', default='postgres')
    define('NEW_ACC_DB_NAME', default='luna_faces')
    define('NEW_ACC_DB_IP', default='127.0.0.1')
    define('NEW_ACC_DB_PORT', default='5432')
    define('NEW_ACC_DB_USER_NAME', default='luna')
    define('NEW_ACC_DB_PASSWORD', default='luna')
    parse_config_file(cmdOptions['config'])

    def getDbDriver(DB_TYPE):
        if DB_TYPE == 'postgres':
            return 'postgres'
        elif DB_TYPE == 'oracle':
            return 'oracle+cx_oracle'

    urlTemplate = '{}://{}:{}@{}:{}/{}'
    return urlTemplate.format(getDbDriver(options.OLD_DB_TYPE), options.OLD_DB_USER_NAME, options.OLD_DB_PASSWORD,
                              options.OLD_DB_IP, options.OLD_DB_PORT, options.OLD_DB_NAME), \
           urlTemplate.format(getDbDriver(options.NEW_DB_TYPE), options.NEW_DB_USER_NAME, options.NEW_DB_PASSWORD,
                              options.NEW_DB_IP, options.NEW_DB_PORT, options.NEW_DB_NAME), \
           urlTemplate.format(getDbDriver(options.NEW_ACC_DB_TYPE), options.NEW_ACC_DB_USER_NAME,
                              options.NEW_ACC_DB_PASSWORD, options.NEW_ACC_DB_IP, options.NEW_ACC_DB_PORT,
                              options.NEW_ACC_DB_NAME)


cmdOptions = getCmdParser()
cleanFlag = cmdOptions['clean']
skipMigration = cmdOptions['skip_migration']
migrateAccountsFlag = cmdOptions['migrate_accounts']
dbOldUrl, dbNewUrl, dbNewAccUrl = initConfig()
oldEngine = create_engine(dbOldUrl, connect_args={"connect_timeout": 5}) if options.OLD_DB_TYPE == 'postgres' else \
    create_engine(dbOldUrl)
newEngine = create_engine(dbNewUrl, connect_args={"connect_timeout": 5}) if options.NEW_DB_TYPE == 'postgres' else \
    create_engine(dbNewUrl)
newAccEngine = create_engine(dbNewAccUrl, connect_args={"connect_timeout": 5}) if options.NEW_ACC_DB_TYPE == 'postgres' \
    else create_engine(dbNewAccUrl)

checkConnectionList = []
if not cleanFlag and not skipMigration:
    checkConnectionList.append([dbOldUrl, baseOld, options.OLD_DB_TYPE])
if not skipMigration:
    checkConnectionList.append([dbNewUrl, baseNew, options.NEW_DB_TYPE])
if migrateAccountsFlag:
    checkConnectionList.append([dbNewAccUrl, baseAccNew, options.NEW_ACC_DB_TYPE])


def checkConnection():
    """
    Check connections to database
    Check required tables in database

    Raises:
        exception if connection to on of database fails or one of required models doesn't exists
    """
    try:
        logger.debug("Check connection to database")
        for dbUrl, dbModelBase, dbType in checkConnectionList:
            if dbType == 'postgres':
                engine = create_engine(dbUrl, connect_args={"connect_timeout": 5})
            else:
                # analogue of connect_timeout for oracle not found or not exists
                engine = create_engine(dbUrl)
            modelsList = [table.__tablename__ for table in dbModelBase.__subclasses__()]
            with engine.begin():
                inspector = Inspector.from_engine(engine)
                tableNames = inspector.get_table_names()
                for modelName in modelsList:
                    if modelName not in tableNames:
                        logger.debug("Connection to \"{}\" model: FAIL".format(modelName))
                        return False
            logger.debug("Connection to Database check success")
    except Exception as e:
        logger.exception()
        logger.error("Error connecting to database: " + str(e))
        exit(1)


def getAllRowsCount(inputTableWithPrimaryKey):
    """
    Get row count in table

    Args:
        inputTableWithPrimaryKey: table model with primary key, example - oldModes.Photo.photo_id

    Returns:
        count of rows in table
    """
    with oldEngine.begin() as connection:
        qr = Query(func.count(inputTableWithPrimaryKey))
        rowCount = connection.execute(qr.statement).cursor.fetchall()[0][0]
    return rowCount


def insertDataIntoTable(dataForInsert, tableModel, engine):
    """
    Insert data into table and raises exceptions if something goes wrong

    Args:
        dataForInsert: list of dict with data for insert
        tableModel: table model to insert data into
        engine: engine for database connection

    Raises:
        exception in something wrongs within insert data into table
    """
    try:
        with engine.begin() as newConnection:
            newConnection.execute(insert(tableModel).values(dataForInsert))
        counters[tableModel.__tablename__]['success'] += len(dataForInsert)
    except IntegrityError:
        counters[tableModel.__tablename__]['errors'] += 1
        logger.exception()
        logger.error('Integrity error in ' + tableModel.__tablename__ + ':' + str(dataForInsert))
    except Exception as e:
        counters[tableModel.__tablename__]['errors'] += 1
        logger.exception()
        logger.error('Error while migrate' + tableModel.__tablename__ + ':' + str(e))
        exit(2)


def insertIntoTable(dataForInsert, tableModel, engine=newEngine):
    """
    Insert data into table depends on db type

    Args:
        dataForInsert: list of dict with data for insert
        tableModel: table model to insert data into
        engine: engine for database connection
    """
    if dataForInsert != list():
        if dbNewUrl.startswith('postgres'):
            insertDataIntoTable(dataForInsert, tableModel, engine)
        else:
            for dataCol in dataForInsert:
                insertDataIntoTable(dataCol, tableModel, engine)
        logger.debug('Complete insert ' + str(
            counters[tableModel.__tablename__]['success']) + ' rows in ' + tableModel.__tablename__)


def getDataForTableFace(lowerBoundary=None):
    """
    Get data from old table for new table

    Args:
        lowerBoundary: field for filter

    Returns:
        list of dicts with data for new table or value of first field to do select with it in the future
    """
    with oldEngine.begin() as oldConnection:
        query = Query([oldModels.Photo.photo_id, oldModels.Photo.person_id, oldModels.Photo.account_id,
                       oldModels.Photo.last_update]).filter(oldModels.Photo.photo_id > lowerBoundary).order_by(
            oldModels.Photo.photo_id.asc()).limit(LIMIT)
        resultPhotos = oldConnection.execute(query.statement).cursor.fetchall()

    return [[{
        'face_id': str(resultPhoto[0]),
        'person_id': str(resultPhoto[1]) if resultPhoto[1] else None,
        'account_id': str(resultPhoto[2]),
        'last_update_time': resultPhoto[3],
        'create_time': resultPhoto[3],
        'attributes_id': str(resultPhoto[0]),
    } for resultPhoto in resultPhotos], resultPhotos[-1][0]]


def getDataForTablePerson(lowerBoundary=None):
    """
    Get data from old table for new table

    Args:
        lowerBoundary: field for filter

    Returns:
        list of dicts with data for new table or value of first field to do select with it in the future
    """
    with oldEngine.begin() as oldConnection:
        query = Query([oldModels.Person.person_id, oldModels.Person.account_id, oldModels.Person.person_info,
                       oldModels.Person.last_update]).filter(oldModels.Person.person_id > lowerBoundary).order_by(
                oldModels.Person.person_id.asc()).limit(LIMIT)
        resultPersons = oldConnection.execute(query.statement).cursor.fetchall()

        return [[{
            'person_id': str(resultPerson[0]),
            'account_id': str(resultPerson[1]),
            'user_data': resultPerson[2],
            'create_time': resultPerson[3],
        } for resultPerson in resultPersons], resultPersons[-1][0]]


def getDataForTableList(lowerBoundary=None):
    """
    Get data from old table for new table

    Args:
        lowerBoundary: field for filter

    Returns:
        list of dicts with data for new table or value of first field to do select with it in the future
    """
    with oldEngine.begin() as oldConnection:
        query = Query([oldModels.AccountList.account_list_id, oldModels.AccountList.account_id,
                       oldModels.AccountList.list_info, oldModels.AccountList.type]).filter(
            oldModels.AccountList.account_list_id > lowerBoundary).order_by(
            oldModels.AccountList.account_list_id.asc()).limit(LIMIT)
        resultLists = oldConnection.execute(query.statement).cursor.fetchall()

        return [[{
            'list_id': str(resultList[0]),
            'account_id': str(resultList[1]),
            'user_data': resultList[2],
            'type': 1 if (resultList[3] == personListType) else 0,
            'create_time': LIST_CREATE_TIME,
            'last_update_time': LIST_CREATE_TIME,
        } for resultList in resultLists], resultLists[-1][0]]


def getDataForTableListFace(listId):
    """
    Get data from old table for new table

    Args:
        listId: id of list to work with

    Returns:
        list of dicts with data for new table
    """
    with oldEngine.begin() as oldConnection:
        query = Query([oldModels.AccountObjectListObject.account_list_id, oldModels.Photo.photo_id,
                       oldModels.Photo.person_id, oldModels.Photo.last_update]
                      ).filter(and_(
            oldModels.AccountObjectListObject.account_list_id == listId,
            oldModels.AccountObjectListObject.account_list_id == oldModels.AccountList.account_list_id,
            oldModels.AccountObjectListObject.object_id == oldModels.Photo.photo_id,
        )).order_by(
            oldModels.AccountList.account_list_id.asc())

        resultListFaces = oldConnection.execute(query.statement).cursor.fetchall()

        return [{
            'list_id': str(resultListFace[0]),
            'face_id': str(resultListFace[1]),
            'person_id': str(resultListFace[2]) if resultListFace[2] else None,
            'last_update_time': resultListFace[3],
        } for resultListFace in resultListFaces]


def getDataForTableListPerson(listId):
    """
    Get data from old table for new table

    Args:
        listId: id of list to work with

    Returns:
        list of dicts with data for new table
    """
    with oldEngine.begin() as oldConnection:
        query = Query(
            [oldModels.AccountObjectListObject.account_list_id, oldModels.Person.person_id]).filter(
            and_(oldModels.AccountObjectListObject.account_list_id == listId,
                 oldModels.AccountObjectListObject.object_id == oldModels.Person.person_id
                 )).order_by(
            oldModels.AccountObjectListObject.account_list_id.asc())

        resultListPersons = oldConnection.execute(query.statement).cursor.fetchall()

        return [{
            'list_id': str(resultListPerson[0]),
            'person_id': str(resultListPerson[1])
        } for resultListPerson in resultListPersons]


def getDataForTableListFaceFromPerson(listId):
    """
    Get data from old table for new table

    Args:
        listId: id of list to work with

    Returns:
        list of dicts with data for new table
    """
    with oldEngine.begin() as oldConnection:
        query = Query(
            [oldModels.AccountObjectListObject.account_list_id, oldModels.Photo.photo_id,
             oldModels.AccountObjectListObject.object_id]).filter(
            and_(oldModels.AccountObjectListObject.account_list_id == listId,
                 oldModels.AccountObjectListObject.object_id == oldModels.Person.person_id,
                 oldModels.AccountObjectListObject.object_id == oldModels.Photo.person_id
                 )).order_by(
            oldModels.AccountObjectListObject.account_list_id.asc())

        resultListPersonsFaces = oldConnection.execute(query.statement).cursor.fetchall()

        return [{
            'list_id': str(resultListPersonFace[0]),
            'face_id': str(resultListPersonFace[1]),
            'person_id': str(resultListPersonFace[2]),
            'last_update_time': LIST_CREATE_TIME,
        } for resultListPersonFace in resultListPersonsFaces]


def migrateTable(getDataFunction, tableModel, oldTablePrimaryKey, listId=None):
    """
    Wrap for migrate table functions

    Args:
        getDataFunction: function that returns data for new table
        tableModel: model name of new table
        oldTablePrimaryKey: primary key from old table
        listId: id of list to work with | only for tables ListFace and ListPerson
    """
    if listId is None:
        logger.debug(' start migration for table {}'.format(tableModel.__tablename__))
    else:
        logger.debug(' start migration with list {} for table {}'.format(listId, tableModel.__tablename__))
    logger.debug('-------------------------------')
    rowCount = getAllRowsCount(oldTablePrimaryKey)
    if listId is not None:
        insertIntoTable(getDataFunction(listId), tableModel)
    else:
        lowerBoundary = '00000000-0000-0000-0000-000000000000'
        for page in range(rowCount // LIMIT + 1):
            data = getDataFunction(lowerBoundary)
            lowerBoundary = data[1]
            insertIntoTable(data[0], tableModel)
    logger.debug('-------------------------------')


class MigrateFunctions:
    """
    Class contain migrate functions for tables: Face, List, Person, ListFace, ListPerson
    """

    @staticmethod
    def migrateFace():
        """
        Migrate Face table
        """
        migrateTable(getDataForTableFace, newModels.Face, oldModels.Photo.photo_id)

    @staticmethod
    def migratePerson():
        """
        Migrate Person table
        """
        migrateTable(getDataForTablePerson, newModels.Person, oldModels.Person.person_id)

    @staticmethod
    def migrateList():
        """
        Migrate List table
        """
        migrateTable(getDataForTableList, newModels.List, oldModels.AccountList.account_list_id)

    @staticmethod
    def migrateLists():
        with oldEngine.begin() as oldConnection:
            query = Query([oldModels.AccountList.account_list_id]
                          ).order_by(
                oldModels.AccountList.account_list_id.asc())

            listIds = [listId[0] for listId in set(oldConnection.execute(query.statement).cursor.fetchall())]

            for listId in listIds:
                query = Query([oldModels.AccountList.type]).filter(
                    oldModels.AccountList.account_list_id == listId).order_by(oldModels.AccountList.account_list_id)
                listType = oldConnection.execute(query.statement).cursor.fetchone()[0]

                if listType is personListType:
                    migrateTable(getDataForTableListPerson, newModels.ListPerson,
                                 oldModels.AccountObjectListObject.account_list_id, listId)
                    migrateTable(getDataForTableListFaceFromPerson, newModels.ListFace,
                                 oldModels.AccountObjectListObject.account_list_id, listId)
                else:
                    migrateTable(getDataForTableListFace, newModels.ListFace,
                                 oldModels.AccountObjectListObject.account_list_id, listId)

    @staticmethod
    def migrateAccount():
        """
        Migrate Account table
        """

        def getDataFromAccountTable(page):
            """
            Get data from old account table
            Args:
                page: page to get data from
            Returns:
                list of rows with data
            """
            with oldEngine.begin() as oldConnection:
                query = Query([oldModels.Account.account_id, oldModels.Account.active, oldModels.Account.password,
                               oldModels.Account.email, oldModels.Account.organization_name]).order_by(
                    oldModels.Account.account_id).offset(page * LIMIT).limit(LIMIT)
                res = oldConnection.execute(query.statement).cursor.fetchall()
                return res

        rowCount = getAllRowsCount(oldModels.Account.account_id)
        for page in range(rowCount // LIMIT + 1):
            insertIntoTable(getDataFromAccountTable(page), newAccModels.Account, newAccEngine)

    @staticmethod
    def migrateAccountToken():
        """
        Migrate Account Token table
        """

        def getDataFromAccountTokenTable(page):
            """
            Get data from old account token table
            Args:
                page: page to get data from
            Returns:
                list of rows with data
            """
            with oldEngine.begin() as oldConnection:
                query = Query([oldModels.AccountToken.token_id, oldModels.AccountToken.account_id,
                               oldModels.AccountToken.token_info]).order_by(
                    oldModels.AccountToken.token_id).offset(page * LIMIT).limit(LIMIT)
                res = oldConnection.execute(query.statement).cursor.fetchall()
                return res

        rowCount = getAllRowsCount(oldModels.AccountToken.token_id)
        for page in range(rowCount // LIMIT + 1):
            insertIntoTable(getDataFromAccountTokenTable(page), newAccModels.AccountToken, newAccEngine)


def dropOldTables():
    """
    Drop old tables
    """
    oldModels.AccountList.__table__.drop(oldEngine)
    oldModels.AccountObjectListObject.__table__.drop(oldEngine)
    oldModels.LunaList.__table__.drop(oldEngine)
    oldModels.LunaListPhoto.__table__.drop(oldEngine)
    oldModels.Person.__table__.drop(oldEngine)
    oldModels.Photo.__table__.drop(oldEngine)
