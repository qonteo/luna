from app.models import Session, Person
import threading

lock = threading.Lock()


def add_person(name: str, uuid: str, password=None):
    with lock:
        session = Session()
        session.add(Person(name, uuid, password))
        session.commit()


def get_person(name):
    with lock:
        session = Session()
        result = session.query(Person.uuid, Person.password).filter(Person.name == name).one()
        return result


def count_persons(name):
    with lock:
        session = Session()
        result = session.query(Person).filter(Person.name == name).count()
        return result
