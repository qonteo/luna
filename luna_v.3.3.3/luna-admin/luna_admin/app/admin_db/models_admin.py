"""
Admin database models.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, Boolean, Sequence
from . import metadata


Base = declarative_base()

taskIdSeq = Sequence('gc_task_task_id_seq', metadata=metadata)
taskErrIdSeq = Sequence('task_error_id_seq', metadata=metadata)


class Admin(Base):
    """
    Admin table
    """
    __tablename__ = 'admin'
    Base.metadata = metadata

    #: admin login
    login = Column(String(128), primary_key=True)

    #: admin password
    password = Column(String(128))

    #: admin email
    email = Column(String(64), unique=True)

    def __repr__(self):
        return '<admin_login %r>' % self.login


class GCTask(Base):
    """
    Admin tasks.
    """
    __tablename__ = 'gc_task'
    Base.metadata = metadata

    start_gc_time = Column(TIMESTAMP)                         #: start task time
    end_gc_time = Column(TIMESTAMP)                           #: end task time
    task_id = Column(Integer, taskIdSeq, primary_key=True)    #: task id
    count_delete_descriptors = Column(Integer)                #: count delete faces for gc
    # descriptors tasks
    count_s3_errors = Column(Integer)                         #: count s3 errors for gc
    # descriptors tasks
    type_dst = Column(String(128))                            #: target of task (all or account + id)
    task_type = Column(Integer, index=True)                   #: task type (2 - gc non-linked
    # faces, 3 - re-extract)
    count_parts = Column(Integer, index=True)                 #: part of task count
    count_done_parts = Column(Integer, index=True)            #: done parts count
    done = Column(Boolean)                                    # : true - tack done, false - cancelled,
    # none - in progress

    def __repr__(self):
        return '<gc_task_task_id %r>' % self.task_id


class TaskError(Base):
    """
    Task errors.
    """
    __tablename__ = 'task_error'
    Base.metadata = metadata

    id = Column(Integer, taskErrIdSeq, primary_key=True)                            #: error id
    task_id = Column(Integer, ForeignKey('gc_task.task_id', ondelete='CASCADE'))     #: task id
    message = Column(String(256))                                     #: message
    code = Column(Integer)                                            #: error code
    error_time = Column(TIMESTAMP)                                    #: error time

    def __repr__(self):
        return '<task_error_id %r>' % self.id
