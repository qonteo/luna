from sqlalchemy import create_engine, Column, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///app.db', echo=False)


Base = declarative_base()


class Person(Base):
    __tablename__ = 'persons'

    # todo increase length of name with length of luna-api person user_data
    name = Column(String(128), primary_key=True, unique=True)
    uuid = Column(String(36))
    password = Column(String(32), default=None, nullable=True)

    def __init__(self, name, uuid, password):
        self.name = name
        self.uuid = uuid
        self.password = password

    def __repr__(self):
        return "<User(name='%s', person_id='%s')>" % (self.name, self.uuid)


if not engine.dialect.has_table(engine, Person.__tablename__):
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
