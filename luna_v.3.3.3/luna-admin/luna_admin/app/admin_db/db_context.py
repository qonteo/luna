"""
Module for work with admin database.

Attributes:
    engine: engine for database

"""

from typing import Optional, List, Union
from sqlalchemy import and_, insert, update, func, desc
from sqlalchemy.orm import Query, sessionmaker
from app.admin_db import engine
from app.admin_db import models_admin as models
from crutches_on_wheels.utils.timer import timer
from datetime import datetime
from enum import Enum
from functools import wraps
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from passlib.hash import pbkdf2_sha256


sessionMaker = sessionmaker(bind=engine)


class TaskType(Enum):
    """
    Enum for task types.
    """
    unknown = 0  #: unknown type
    descriptorsGC = 2  #: gc non-linked faces
    reExtractGC = 3  #: re-extract descriptors


def exceptionWrap(wrapFunc):
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


def createAdmin() -> None:
    """
    Create default admin with login and password "root".
    """
    with engine.begin() as connection:
        connection.execute(insert(models.Admin).values(login='root', password=pbkdf2_sha256.hash("root"), email=''))


class AdminSession:
    """
    Context manager for work with admin database

    Attributes:
        session: session to admin database
    """

    def __init__(self):
        global sessionMaker
        self.session = sessionMaker()

    def __enter__(self):
        """
        Enter context manager

        Returns:
            return session
        """
        return self.session

    def __exit__(self, *args):
        """
        Exit context manager

        Close session.

        Args:
            *args: params

        """
        self.session.close()


class DBContext:
    """
    DB context

    Attributes:
        logger: request logger
    """

    def __init__(self, logger):
        self.logger = logger

    @exceptionWrap
    def changeAdminPassword(self, newPassword: str) -> None:
        """
        Change admin password.

        Args:
            newPassword: new password
        """
        pwdHash = pbkdf2_sha256.hash(newPassword)
        with engine.begin() as connection:
            updPwd = update(models.Admin).values({'password': pwdHash})
            connection.execute(updPwd.statement)

    @exceptionWrap
    def authAdmin(self, login: str, password: str) -> bool:
        """
        Verify admin login and password

        Args:
            login: login
            password: password

        Returns:
            true for valid auth date, False otherwise.
        """
        with engine.begin() as connection:
            query = Query([models.Admin.login, models.Admin.password])
            resLogin, resPassword = connection.execute(query.statement).cursor.fetchone()
        return pbkdf2_sha256.verify(password, resPassword) and login == resLogin

    @exceptionWrap
    def createTask(self, taskType: TaskType, distType: str) -> int:
        """
        Create new task.

        Args:
            taskType: task type
            distType: target

        Returns:
            task id
        """
        with AdminSession() as session:
            task = models.GCTask()
            task.type_dst = distType
            task.task_type = taskType.value
            task.start_gc_time = datetime.now()
            task.count_duplicate_error = 0
            task.count_non_attach_error = 0
            task.count_delete_descriptors = 0
            task.count_s3_errors = 0
            task.count_done_parts = 0
            task.count_parts = 1
            task.count_link_with_non_exist_object = 0
            session.add(task)
            session.commit()
            return task.task_id

    @exceptionWrap
    @timer
    def patchTask(self, taskId: int, content: dict) -> None:
        """
        Patch task.

        Args:
            taskId: task id
            content: dict with content
        """
        for countName in ["count_delete_descriptors", "count_s3_errors"]:
            if countName not in content:
                content[countName] = 0

        with engine.begin() as connection:

            tab = models.GCTask.__table__
            connection.execute(tab.update().where(tab.c.task_id == taskId).values(
                count_delete_descriptors=tab.c.count_delete_descriptors + content["count_delete_descriptors"],
                count_s3_errors=tab.c.count_s3_errors + content["count_s3_errors"]).compile(
                compile_kwargs={'literal_binds': True}))

    @exceptionWrap
    @timer
    def finishTask(self, taskId: int, done: bool = True) -> None:
        """
        Finish task.

        Args:
            taskId: task id
            done: true - task done, false - task cancelled
        """
        with engine.begin() as connection:
            stInsert = update(models.GCTask).where(models.GCTask.task_id == taskId).values(
                end_gc_time=datetime.now(), done=done)
            connection.execute(stInsert)

    @exceptionWrap
    def finishTaskIfNeed(self, taskId, done) -> None:
        """
        Finish task, if it in processing.

        Args:
            taskId: task id
            done: true - task done, false - task cancelled
        """
        with engine.begin() as connection:
            updateSt = update(models.GCTask).where(
                and_(models.GCTask.task_id == taskId, models.GCTask.done == None)).values(
                end_gc_time=datetime.now(), done=done)
            connection.execute(updateSt)

    @exceptionWrap
    def stopAllTask(self) -> None:
        """
        Cancel all task which is in processing.
        """
        with engine.begin() as connection:
            stInsert = update(models.GCTask).where(models.GCTask.done == None).values(
                end_gc_time=datetime.now(), done=False)
            connection.execute(stInsert)

    @exceptionWrap
    @timer
    def finishPartOfTask(self, taskId: int, countParts: int = 1) -> None:
        """
        Update task progress and finish it if all parts is done.

        Args:
            taskId: task id
            countParts: count completed task parts
        """
        with engine.begin() as connection:
            tab = models.GCTask.__table__
            clCount = engine.execute(tab.update().returning(tab.c.count_done_parts).where(
                and_(tab.c.task_id == taskId, tab.c.done == None)).values(
                count_done_parts=tab.c.count_done_parts + countParts).compile(
                compile_kwargs={'literal_binds': True})).fetchone()
            if clCount is None:
                return
            clCount = clCount[0]

            query = Query(models.GCTask.count_parts).filter(models.GCTask.task_id == taskId)
            res = connection.execute(query.statement)
            pratsCount = res.cursor.fetchone()[0]

            if clCount >= pratsCount:
                self.finishTask(taskId, True)

    @exceptionWrap
    @timer
    def setCountOfParts(self, taskId: int, countParts: int) -> None:
        """
        Set parts task count.

        Args:
            taskId: task id
            countParts: parts count
        """
        with engine.begin() as connection:
            updateCntParts = update(models.GCTask).where(models.GCTask.task_id == taskId).values(count_parts=countParts)
            connection.execute(updateCntParts)

    @exceptionWrap
    @timer
    def putError(self, taskId, errorCode, msg):
        with engine.begin() as connection:
            stInsert = insert(models.TaskError).values(message=msg, code=errorCode,
                                                       task_id=taskId, error_time=datetime.now())
            connection.execute(stInsert)

    @exceptionWrap
    @timer
    def getTask(self, taskId: int) -> Union[models.GCTask, None]:
        """
        Get task.

        Args:
            taskId: task id

        Returns:
            None if task not found, task otherwise
        """
        with AdminSession() as session:
            task = session.query(models.GCTask).filter(models.GCTask.task_id == taskId).first()
            return task

    @exceptionWrap
    def getCountTasks(self, taskType: Optional[TaskType] = None) -> int:
        """
        Get task count

        Args:
            taskType: task type

        Returns:
            task count

        """
        with AdminSession() as session:
            res = session.query(func.count(models.GCTask.task_id)).filter(
                models.GCTask.task_type == taskType.value if taskType is not None else True).first()[0]
            return res

    @exceptionWrap
    def getTasks(self, page: int, pageSize: int, taskType: Optional[TaskType] = None) -> List[dict]:
        """
        Get tasks  with pagination.

        Args:
            page: number of page
            pageSize: count tasks on page
            taskType: task type

        Returns:
            list with tasks. tasks are represented in pretty view.
        """
        with AdminSession() as session:
            tasks = session.query(models.GCTask).filter(
                models.GCTask.task_type == taskType.value if taskType is not None else True).order_by(
                desc(models.GCTask.start_gc_time)).offset((page - 1) * pageSize).limit(
                pageSize).all()

            return [self.prepareTaskToRender(task) for task in tasks]

    @exceptionWrap
    def getGCTask(self, taskId: int) -> Union[dict, None]:
        """
        Get task in pretty view

        Args:
            taskId: task if

        Returns:
            None if task not found, pretty task otherwise
        """
        task = self.getTask(taskId)
        if task is None:
            return task
        return self.prepareTaskToRender(task)

    @exceptionWrap
    def getCountTasksErrors(self, ids: List[int]) -> list:
        """
        Get tasks error cont

        Args:
            ids: task ids

        Returns:
            list with count errors.
        """
        with AdminSession() as session:
            res = session.query(func.count(models.TaskError.id)).filter(and_(models.TaskError.task_id.in_(ids))).all()
            return [count[0] for count in res]

    @exceptionWrap
    def getTasksErrors(self, ids: List[int], page: int, pageSize: int) -> List[models.TaskError]:
        """
        Get tasks errors with pagination.

        Args:
            ids: task ids
            page: page
            pageSize: page size

        Returns:
            list task errors
        """
        with AdminSession() as session:
            res = session.query(models.TaskError).filter(and_(models.TaskError.task_id.in_(ids))).offset(
                (page - 1) * pageSize).limit(pageSize).all()
            return res

    @exceptionWrap
    def prepareTaskToRender(self, task: models.GCTask) -> dict:
        """
        Make pretty view of task.

        Args:
            task: task

        Returns:
            task
        """
        info = {"start_time": task.start_gc_time.isoformat("T").split(".")[0] + "Z"}
        if task.end_gc_time is None:
            info["duration"] = "in progress"
        else:
            info["duration"] = str((task.end_gc_time - task.start_gc_time)).split(".")[0]

        info["status"] = task.done
        taskDetail = {}

        if task.task_type == TaskType.descriptorsGC.value:
            taskType = "removing old descriptors"
            taskDetail["count_delete_descriptors"] = task.count_delete_descriptors
            taskDetail["count_s3_errors"] = task.count_s3_errors
        else:
            taskType = "re-extract descriptors"
            taskDetail["re-extract descriptors"] = task.count_delete_descriptors

        info["target"] = task.type_dst
        info["task_id"] = task.task_id
        info["error_count"] = self.getCountTasksErrors([task.task_id])[0]
        if task.count_parts == 0:
            info["progress"] = 1
        else:
            info["progress"] = round(task.count_done_parts / task.count_parts, 2)
        return {"task_info": info, "task_type": taskType, "task_detail": taskDetail}

    @exceptionWrap
    def prepareErrorOfTaskToRender(self, taskId: int, page: int, pageSize: int) -> dict:
        """
        Get errors of task  in pretty view.

        Args:
            taskId: task id
            page: error page
            pageSize: error page size

        Returns:
            dict with errors and error count
        """
        task = self.getTask(taskId)
        if task is None:
            return {"errors": [], "task_info": {}}
        res = []

        errors = self.getTasksErrors([taskId], page, pageSize)
        for error in errors:
            errorForRender = {"message": str(error.message), "error_time": str(error.error_time).split(".")[0],
                              "code": error.code, "id": error.id}
            if task.task_type == TaskType.descriptorsGC.value:
                errorForRender["task_type"] = "removing old descriptors"
            else:
                errorForRender["task_type"] = "re-extract descriptors"
            res.append(errorForRender)
        return {"errors": res, "error_count": self.getCountTasksErrors([taskId])[0]}
