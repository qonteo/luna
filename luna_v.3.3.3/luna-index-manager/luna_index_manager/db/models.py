from enum import IntEnum
from typing import List

from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import metadata, engine


Base = declarative_base()
TASK_SEQUENCE = Sequence('index_log_task_id_seq', start=1)
ERROR_SEQUENCE = Sequence('error_error_id_seq', start=1)


class TaskStatus(IntEnum):
    """
    Enum for status of task.
    """
    SUCCESS = 0  #: success, new index exists on 1 or more matcher
    FAILED = 1  #: task failed
    CANCELLED = 2  #: task was cancelled


class IndexTaskLog(Base):
    """
    Database table model for index task log.
    """
    __tablename__ = 'index_log'
    Base.metadata = metadata

    #: Column(Integer): task id, autoincrement
    task_id = Column(Integer, TASK_SEQUENCE, primary_key=True)

    #: Column(String): generation name from indexer
    generation = Column(String(128), index=True)

    #: Column(String): id of the indexed list of luna-faces, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9a-b}xx-xxxxxxxxxxxx"
    list_id = Column(String(36), index=True)

    #: Column(Integer): status of task 0 - success done, 1 - failed, 2 - cancelled
    status = Column(Integer, index=True)

    #: Column(DateTime): start time of the index step
    start_index_time = Column(DateTime, index=True)

    #: Column(DateTime): end time of the index step
    end_index_time = Column(DateTime, index=True)

    #: Column(DateTime): start time of the index upload step
    start_upload_index_time = Column(DateTime, index=True)

    #: Column(DateTime): end time of the index upload  step
    end_upload_index_time = Column(DateTime, index=True)

    #: Column(DateTime): start time of the index reload step
    start_reload_index_time = Column(DateTime, index=True)

    #: Column(DateTime): end time of the index reload step
    end_reload_index_time = Column(DateTime, index=True)

    #: Column(DateTime): task start time
    start_time = Column(DateTime, index=True)

    #: Column(DateTime): task end time
    end_time = Column(DateTime, index=True)

    #: Column(DateTime): task last update time
    last_update_time = Column(DateTime, index=True)

    @classmethod
    def getColumnNames(cls) -> List[str]:
        """
        Get all column name of table.

        Returns:
            list of column name in order as  in db
        """
        return cls.__table__.columns._data._list

    def __repr__(self):
        return '<Index log %r>' % self.task_id


class Error(Base):
    """
    Database table model for task errors.
    """
    __tablename__ = 'error'
    Base.metadata = metadata

    #: Column(Integer): error id, autoincrement
    error_id = Column(Integer, ERROR_SEQUENCE, primary_key=True)

    #: Column(Integer): task id which gave rise to the error
    task_id = Column(Integer, ForeignKey('index_log.task_id', ondelete='CASCADE'), unique=True)

    #: Column(DateTime): error time
    error_time = Column(DateTime)

    #: Column(DateTime): error message
    message = Column(String(1024))

    @classmethod
    def getColumnNames(cls) -> List[str]:
        """
        Get all column name of table.

        Returns:
            list of column name in order as  in db
        """
        return cls.__table__.columns._data._list

    def __repr__(self):
        return '<Error %r>' % self.error_id


Session = sessionmaker(bind=engine, autocommit=True)
