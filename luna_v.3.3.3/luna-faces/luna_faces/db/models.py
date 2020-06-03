from sqlalchemy import Column, String, Integer, ForeignKey, TIMESTAMP, Sequence, DateTime, func, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from . import metadata, engine

Base = declarative_base()
LINK_SEQUENCE = Sequence('link_key', start=1)
UNLINK_SEQUENCE = Sequence('unlink_key', start=1)


class Face(Base):
    """
    Database table model for faces.
    """
    __tablename__ = 'face'
    __table_args__ = {'comment': 'Table of faces.'}
    Base.metadata = metadata

    #: str: face id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    face_id = Column(String(36), primary_key=True, comment="uuid4: face id")

    #: str: attributes id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    attributes_id = Column(String(36), index=True, unique=True, comment="uuid4: face attributes id", nullable=False)

    #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    account_id = Column(String(36), index=True, comment="uuid4: id of the account to which the face belongs")

    # : str: event id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx", reference to event which created
    # the face
    event_id = Column(String(36), index=True, comment="uuid4: id of the event that caused the face creation")

    #: str: client info about the face
    user_data = Column(String(128), index=True, comment="str: face user data")

    #: DateTime: date and time of creating face
    create_time = Column(TIMESTAMP, comment="date: face creation time")

    #: DateTime: date and time of last changed of the face
    last_update_time = Column(TIMESTAMP, index=True, comment="date: last update time of face")

    #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    person_id = Column(String(36), index=True, comment="uuid4: id of person to which the face is attached")

    #: str: external id of the face, if it has its own mapping in external system
    external_id = Column(String(36), index=True, comment="str: the face external id")

    def __repr__(self):
        return '<Faces %r>' % self.face_id


class Person(Base):
    """
    Database table model for persons.
    """
    __tablename__ = 'person'
    __table_args__ = {'comment': 'Table of persons.'}
    Base.metadata = metadata

    #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    person_id = Column(String(36), primary_key=True, comment="uuid4: person id")

    #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    account_id = Column(String(36), index=True, comment="uuid4: id of the account to which the person belongs")

    #: str: client info about the face
    user_data = Column(String(128), index=True, comment="str: person user data")

    #: DateTime: date and time of creating face
    create_time = Column(TIMESTAMP, comment="date: person create time")

    #: str: external id of the person, if it has its own mapping in external system
    external_id = Column(String(36), index=True, comment="str: person external id")

    def __repr__(self):
        return '<Persons %r>' % self.person_id


class List(Base):
    """
    Database table model for lists.
    """
    __tablename__ = 'list'
    __table_args__ = {'comment': 'Table of lists.'}
    Base.metadata = metadata

    #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    list_id = Column(String(36), primary_key=True, comment="uuid4: list id")

    #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    account_id = Column(String(36), index=True, comment="uuid4: id of the account to which the list belongs")

    #: str: client info about the list
    user_data = Column(String(128), index=True, comment="str: list user data")

    #: integer: type of list (persons - 1, faces - 0)
    type = Column(Integer, default=1, index=True, comment="int: list type: 0 - face list, 1 - person list")

    #: DateTime: date and time of creating list
    create_time = Column(TIMESTAMP, index=True, comment="date: list create time")

    #: DateTime: date and time of last changed of the list
    last_update_time = Column(TIMESTAMP, index=True, comment="date: last update time of the list")

    def __repr__(self):
        return '<Lists %r>' % self.list_id


class ListFace(Base):
    """
    Database table model for links between faces and lists.
    """
    __tablename__ = 'list_face'
    __table_args__ = {'comment': 'Relationship table for lists and faces.'}
    Base.metadata = metadata

    #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), primary_key=True,
                     comment="uuid4: list id")

    #: str: face id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    face_id = Column(String(36), ForeignKey('face.face_id', ondelete='CASCADE'), primary_key=True, index=True,
                     comment="uuid4: face id")

    #: str: reference to person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    person_id = Column(String(36), index=True, comment="uuid4: person id")

    #: DateTime: date and time of last attach/detach face to list
    last_update_time = Column(TIMESTAMP, index=True, comment="uuid4: last update time of list and face relation")

    #: int: number of link face to list
    link_key = Column(Integer, LINK_SEQUENCE, index=True, comment="int: list and face relation key")

    def __repr__(self):
        return '<listface_list_id %r>' % self.list_id


Index('index_list_id_link_key', ListFace.list_id, ListFace.link_key.desc())


class ListPerson(Base):
    """
    Database table model for links between persons and lists.
    """
    __tablename__ = 'list_person'
    __table_args__ = {'comment': 'Relationship table for lists and persons.'}
    Base.metadata = metadata

    #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), primary_key=True,
                     comment="uuid4: list id""")

    #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    person_id = Column(String(36), ForeignKey('person.person_id', ondelete='CASCADE'), primary_key=True, index=True,
                       comment="uuid4: person id")

    def __repr__(self):
        return '<listperson_list_id %r>' % self.list_id


class UnlinkAttributesLog(Base):
    """
    Database table model for history attach and detach attributes to lists.
    """
    __tablename__ = 'unlink_attributes_log'
    __table_args__ = {'comment': 'Log of face and list links deletions.'}
    Base.metadata = metadata

    #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), index=True, comment="uuid4: list id")

    #: str: attributes id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
    attributes_id = Column(String(36), index=True, comment="uuid4: attributes id", nullable=False)

    #: int: number of link face to list
    link_key = Column(Integer, index=True, unique=True, comment="int: link id")

    #: int: number of unlink face to list
    unlink_key = Column(Integer, UNLINK_SEQUENCE, primary_key=True, comment="int: id of link deletion")

    #: DateTime: date and time of detach attributes from list
    update_time = Column(TIMESTAMP, server_default=func.now(), index=True, comment="date: last update time")


Index('index_list_id_unlink_key', UnlinkAttributesLog.list_id, UnlinkAttributesLog.unlink_key.desc())

Session = sessionmaker(bind=engine, autocommit=True)
