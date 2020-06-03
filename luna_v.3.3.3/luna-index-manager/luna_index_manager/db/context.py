from datetime import datetime
from functools import wraps
from typing import List, Optional, Tuple

from sqlalchemy import and_, insert, update, func
from sqlalchemy.orm import Query

from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.functions import convertTimeToString
from db import engine, models
from db.models import IndexTaskLog, TaskStatus
from logbook import Logger

ALL_LISTS = "all"

def exceptionWrap(wrapFunc: callable) -> callable:
    """
    Decorator for catching exceptions when composing queries to the database.

    Args:
        wrapFunc: function

    Returns:
        If exception is not caught, function result is returned, else Result\
        with value of exception is returned
    """

    @wraps(wrapFunc)
    def wrap(*func_args, **func_kwargs):
        try:
            return wrapFunc(*func_args, **func_kwargs)
        except VLException:
            raise
        except Exception as e:
            func_args[0].logger.exception()
            raise VLException(Error.ExecuteError)

    return wrap


def getTaskInfoAsDict(taskRow: Tuple) -> dict:
    """
    Convert task tuple from db to dict
    Args:
        taskRow: task row (with error_time, message and error_id)

    Returns:
        dict, keys are IndexTaskLog column name + error, values are value of corresponding column  from IndexTaskLog +
        dict with error

    """
    res = dict(zip(IndexTaskLog.getColumnNames() + ["error_time", "error_message"], taskRow[:-3]))
    if taskRow[-3] is not None:
        res["error"] = dict(zip(["error_time", "error_message"], taskRow[-2:]))
        res["error"]["error_time"] = convertTimeToString(res["error"]["error_time"])
    else:
        res["error"] = None
    for name, value in res.items():
        if name.endswith("time"):
            if value is not None:
                res[name] = convertTimeToString(value)
    return res


class DBContext:
    """
    DB context

    Attributes:
        logger: request logger
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    @exceptionWrap
    def createNewTask(self, listId: str) -> int:
        """
        Create new task in db

        Args:
            listId: indexed list id

        Returns:
            task id
        """
        with engine.begin() as connection:
            createTime = datetime.now()
            lastUpdate = datetime.now()
            insertSt = insert(models.IndexTaskLog).values(list_id=listId, start_time=createTime,
                                                          last_update_time=lastUpdate)
            res = connection.execute(insertSt)
            taskId = res.inserted_primary_key[0]
            return taskId

    @exceptionWrap
    def updateTaskData(self, taskId: int, **kwargs) -> None:
        """
        Update task data.

        Args:
            taskId: task id

        Keyword Args:
            generation (str): generation name from indexer
            status (int): status of task 0 - success done, 1 - failed, 2 - cancelled
            start_index_time (datetime): start time of the index step
            end_index_time (datetime): end time of the index step
            start_upload_index_time (datetime): start time of the index upload step
            end_upload_index_time (datetime): end time of the index upload  step
            start_reload_index_time (datetime): end time of the index reload step
            end_reload_index_time (datetime): end time of the index reload step
            end_time (datetime): task end time
            last_update_time (datetime): task last update time
        """
        lastUpdate = datetime.now()
        with engine.begin() as connection:
            kwargs["last_update_time"] = lastUpdate
            updateFaceSt = update(models.IndexTaskLog).where(models.IndexTaskLog.task_id == taskId).values(**kwargs)
            connection.execute(updateFaceSt)

    @exceptionWrap
    def putError(self, taskId: int, msg: str) -> int:
        """
        Put task error

        Args:
            taskId: task id
            msg: error message

        Returns:
            error id
        """
        with engine.begin() as connection:
            errorTime = datetime.now()
            insertSt = insert(models.Error).values(task_id=taskId, message=msg, error_time=errorTime)
            res = connection.execute(insertSt)
            taskId = res.inserted_primary_key[0]
            return taskId

    @exceptionWrap
    def getTask(self, taskId: int) -> dict:
        """
        Get task by id

        Args:
            taskId: task id

        Returns:
            dict, keys are IndexTaskLog column name + error, values are value of corresponding column  from IndexTaskLog +
            dict with error
        Raises:
            VLException(Error.IndexTaskNotFouns, 404, isCriticalError=False): if task not found
        """
        with engine.begin() as connection:
            query = Query(models.IndexTaskLog.__table__.columns + [models.Error.error_id,
                                                                   models.Error.error_time, models.Error.message])
            query = query.outerjoin(models.Error).filter(models.Error.task_id == models.IndexTaskLog.task_id)
            query = query.filter(models.IndexTaskLog.task_id == taskId)
            res = connection.execute(query.statement)
            taskRow = res.cursor.fetchone()
            if taskRow is None:
                raise VLException(Error.IndexTaskNotFound, 404, isCriticalError=False)
            return dict(zip(IndexTaskLog.getColumnNames(), taskRow))

    @exceptionWrap
    def isTaskForListInProgress(self, listId: str) -> bool:
        """
        Check that current task works with listId
        Returns:
            true if current task works with list else false
        """
        with engine.begin() as connection:
            query = Query(models.IndexTaskLog.task_id).filter(and_(models.IndexTaskLog.list_id == listId,
                                                                   models.IndexTaskLog.status == None))
            res = len(connection.execute(query.statement).cursor.fetchall()) > 0
            return res

    @exceptionWrap
    def searchTasks(self, page: int = 1, pageSize: int = 100, generations: Optional[List[str]] = None,
                    listIds: Optional[List[str]] = None, status=None) -> Tuple[List[dict], int]:
        """
        Search tasks

        Args:
            page: page number
            pageSize: page size
            generations: list of generations
            listIds: list ids
            status: status of rask

        Returns:
            list of dict (keys are IndexTaskLog column name + error, values are value of corresponding column  from IndexTaskLog +
            dict with error) and task count
        """
        with engine.begin() as connection:
            filters = and_(IndexTaskLog.list_id.in_(listIds) if listIds is not None else True,
                           IndexTaskLog.generation.in_(generations) if generations is not None else True,
                           IndexTaskLog.status == status if status is not None else True)
            query = Query(models.IndexTaskLog.__table__.columns + [models.Error.__table__.columns.error_id,
                                                                   models.Error.__table__.columns.error_time,
                                                                   models.Error.__table__.columns.message])
            query = query.outerjoin(models.Error)
            query = query.filter(filters)

            query = query.order_by(IndexTaskLog.start_time.desc()).offset((page - 1) * pageSize).limit(pageSize)
            res = connection.execute(query.statement)
            taskRows = res.cursor.fetchall()
            queryCount = Query([func.count(IndexTaskLog.task_id).label('count')]).filter(filters)
            count = connection.execute(queryCount.statement).cursor.fetchone()[0]

            return [getTaskInfoAsDict(taskRow) for taskRow in taskRows], count

    @exceptionWrap
    def getTaskError(self, taskId: int) -> Optional[dict]:
        """
        Get task error.

        Args:
            taskId: task id

        Returns:
             dict, keys are Error column name, values are value of corresponding column if error exist otherwise None.
        """
        with engine.begin() as connection:
            query = Query(models.Error)
            query = query.filter(models.Error.task_id == taskId)
            res = connection.execute(query.statement)
            errorRow = res.cursor.fetchone()
            if errorRow is None:
                return None
            return dict(zip(models.Error.getColumnNames(), errorRow))

    @exceptionWrap
    def getCurrentGenerations(self) -> Optional[dict]:
        """
        Get list ids and last successful generations for them.

        Returns:
            dict, key - list id, value - generations
        """
        with engine.begin() as connection:
            query = Query([models.IndexTaskLog.list_id, func.max(models.IndexTaskLog.generation).label('max')])
            query = query.filter(and_(models.IndexTaskLog.status == TaskStatus.SUCCESS.value,
                                      models.IndexTaskLog.generation != None)).group_by(
                models.IndexTaskLog.list_id)
            res = connection.execute(query.statement)
            generationAndLists = res.cursor.fetchall()
            return dict(generationAndLists)

    @exceptionWrap
    def getStartAndUploadIndexTime(self, listId: str) -> Optional[Tuple[datetime, Optional[datetime]]]:
        """
        Get start index time and upload index time for list with listId

        Args:
            listId: list id
        Returns:
            tuple with start index time and upload index time
        """
        with engine.begin() as connection:
            query = Query([models.IndexTaskLog.__table__.columns.start_index_time,
                           models.IndexTaskLog.__table__.columns.start_upload_index_time]).filter(
                and_(models.IndexTaskLog.list_id == listId)).order_by(
                models.IndexTaskLog.start_time.desc())
            res = connection.execute(query.statement).cursor.fetchone()
            if res is not None and res[0] is None:
                return None
        return res

    @exceptionWrap
    def getSuccessStartIndexTimeOfList(self, listId: str) -> Optional[datetime]:
        """
        Get start index time of last success upload to matchers index.

        Args:
            listId: list id
        Returns:
            start index time
        """
        with engine.begin() as connection:
            query = Query([models.IndexTaskLog.__table__.columns.start_index_time]).filter(
                and_(models.IndexTaskLog.list_id == listId,
                     models.IndexTaskLog.status == TaskStatus.SUCCESS.value)).order_by(
                models.IndexTaskLog.start_time.desc())
            res = connection.execute(query.statement).cursor.fetchone()
            if res is None:
                return None
            return res[0]

    @exceptionWrap
    def isIndexesUploadToMatcher(self) -> bool:
        """
        Determinate if there are matchers with indexes.

        Returns:
            true if last time success reloaded indexes is greater than last failed reload indexes time otherwise false
        """
        with engine.begin() as connection:
            query = Query(func.max(models.IndexTaskLog.end_index_time).label('max'))
            query = query.filter(and_(models.IndexTaskLog.status != TaskStatus.SUCCESS.value,
                                      models.IndexTaskLog.end_index_time != None))

            res = connection.execute(query.statement)
            lastFailedReloadIndexesTime = res.cursor.fetchone()

            query = Query(func.max(models.IndexTaskLog.end_index_time).label('max'))
            query = query.filter(and_(models.IndexTaskLog.status == TaskStatus.SUCCESS.value))

            res = connection.execute(query.statement)
            lastSuccessReloadIndexesTime = res.cursor.fetchone()

            if lastSuccessReloadIndexesTime is None or lastSuccessReloadIndexesTime[0] is None:
                return False
            if lastFailedReloadIndexesTime is None or lastFailedReloadIndexesTime[0] is None:
                return True
            return lastSuccessReloadIndexesTime[0] > lastFailedReloadIndexesTime[0]

    @exceptionWrap
    def updateTasksNullStatus(self) -> None:
        """
        Set 'failed' status to tasks with 'null' status after statring service
        """
        with engine.begin() as connection:
            query = Query(models.IndexTaskLog.task_id).filter(models.IndexTaskLog.status == None)
            taskIds = connection.execute(query.statement).cursor.fetchall()

            errorTime = datetime.now()
            for taskId in taskIds:
                query = insert(models.Error).values(task_id=taskId, message='Service stoped while indexing',
                                                    error_time=errorTime)
                connection.execute(query)

            query = update(models.IndexTaskLog).where(models.IndexTaskLog.status == None).values(
                status=TaskStatus.FAILED.value)
            connection.execute(query)
