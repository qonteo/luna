from sqlalchemy import Column, Boolean, String, ForeignKey, Integer, DateTime, TIMESTAMP, Sequence, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

baseOld = declarative_base()
baseNew = declarative_base()
baseAccNew = declarative_base()

LINK_SEQUENCE = Sequence('link_key', start=1)
UNLINK_SEQUENCE = Sequence('unlink_key', start=1)


class oldModels:
    """
    Old models from luna api v.2
    """
    class Account(baseOld):
        """
        Database table model for account.
        """
        __tablename__ = 'account'

        #: uuid4:  account id.
        account_id = Column(UUID(as_uuid=True), primary_key=True, unique=True)

        #: bool: account status (blocked or not).
        active = Column(Boolean)

        #: str:  hash from account password. Encryption algorithm is pbkdf2_sha256 from passlib.
        password = Column(String(128))

        #: str: account email.
        email = Column(String(64), unique=True)

        #: str: organization name account represents.
        organization_name = Column(String(128))

        def fillAccount(self, tup) -> baseOld:
            """
            Fill account data from array of elements

            :param tup: array with elements (id, active status, password, e-mail, organization name).
            :return: self
            """

            self.account_id = tup[0]
            self.active = tup[1]
            self.password = tup[2]
            self.email = tup[3]
            self.organization_name = tup[4]
            return self

        def __repr__(self):
            return '<Accounts %r>' % self.account_id

    class Person(baseOld):
        """
        Persons table
        """
        __tablename__ = 'person'

        person_id = Column(UUID(as_uuid=True), primary_key=True, unique=True)
        #: uuid4: account id person is linked to
        account_id = Column(UUID(as_uuid=True), ForeignKey('account.account_id', ondelete='CASCADE'))

        #: str: person info
        person_info = Column(String(128))

        #: integer:  person status
        state = Column(Integer, default=0)

        #: DateTime: creation time of person
        last_update = Column(DateTime)

        def fillPerson(self, tup) -> baseOld:
            self.person_id = tup[0]
            self.account_id = tup[1]
            self.person_info = tup[2]
            return self

        def __repr__(self):
            return '<Persons %r>' % self.person_id

    class Photo(baseOld):
        """
        Table of photos
        """
        __tablename__ = 'photo'

        #: uuid4: descriptor id from LUNA
        photo_id = Column(UUID(as_uuid=True), primary_key=True, unique=True)

        #: uuid4: person id, descriptor is linked to
        person_id = Column(UUID(as_uuid=True), index=True)

        #: uuid4: account id, descriptor is linked to
        account_id = Column(UUID(as_uuid=True), ForeignKey('account.account_id', ondelete='CASCADE'))

        #: DateTime: date and time of last attach/detach of descriptor
        last_update = Column(DateTime)

        #: int: number of links from descriptor lists or person lists
        ref = Column(Integer, default=0, index=True)

        def __repr__(self):
            return '<Photo %r>' % self.photo_id

    class AccountToken(baseOld):
        """
        Token table.
        """
        __tablename__ = 'account_token'

        #: uuid4: token id
        token_id = Column(UUID(as_uuid=True), primary_key=True, unique=True)

        #: uuid4: account id, token is linked to
        account_id = Column(UUID(as_uuid=True), ForeignKey('account.account_id', ondelete='CASCADE'))

        #: str: string with token data
        token_info = Column(String(128))

        def __repr__(self):
            return '<Accounttoken %r>' % self.token_id

    class AccountList(baseOld):
        """
        Account list.
        """
        __tablename__ = 'account_list'

        #: uuid4: account list id
        account_list_id = Column(UUID(as_uuid=True), primary_key=True)

        #: uuid4: account id, list is linked to
        account_id = Column(UUID(as_uuid=True), ForeignKey('account.account_id', ondelete='CASCADE'), index=True)

        #: int: number of LUNA lists, which correspond to current list
        key_luna_list = Column(Integer, default=0)

        #: bool: list type (person list or descriptor list)
        type = Column(Boolean, default=True)

        #: int: list status, when objects are modified
        state = Column(Integer, default=0)

        #: str: list data
        list_info = Column(String(128))

        def __repr__(self):
            return '<Accountlist %r>' % self.account_list_id

    class LunaList(baseOld):
        """
        List table in LUNA
        """
        __tablename__ = 'luna_list'

        #: uuid4: list id from LUNA
        list_id = Column(UUID(as_uuid=True), unique=True, index=True)

        #: bool: list status (if number of persons > MAX_PERSON_IN_LIST, no more objects can be added to the list)
        state = Column(Boolean, default=True)

        #: uuid4: account list id, account is linked to
        account_list_id = Column(UUID(as_uuid=True),
                                    ForeignKey('account_list.account_list_id', ondelete='CASCADE'),
                                    primary_key=True)

        #: int: list count, corresponded with account_list_id (used to avoid duplication of lists while race)
        count_account_list = Column(Integer, primary_key=True)

        #: int: number of descriptors, linked to the list
        count_photo_in_list = Column(Integer, default=0)

        def __repr__(self):
            return '<List %r>' % self.list_id

    class AccountObjectListObject(baseOld):
        """
        Table, which contains links between objects (persons or descriptors) and lists from LUNA
        """
        __tablename__ = 'account_object_list_object'

        #: uuid4: object id
        object_id = Column(UUID(as_uuid=True), primary_key=True)

        #: uuid4: account list id
        account_list_id = Column(UUID(as_uuid=True),
                                    ForeignKey('account_list.account_list_id', ondelete='CASCADE'),
                                    primary_key=True)

        def __repr__(self):
            return '<AccountObjectListObject %r>' % self.account_list_id

    class LunaListPhoto(baseOld):
        """
        Table, which contains links between descriptors and lists from LUNA (for deletion).
        """
        __tablename__ = 'luna_list_photo'

        #: uuid4:  descriptor id
        photo_id = Column(UUID(as_uuid=True), ForeignKey('photo.photo_id', ondelete='CASCADE'), primary_key=True)

        #: uuid4: list id in LUNA.
        luna_list_id = Column(UUID(as_uuid=True), ForeignKey('luna_list.list_id', ondelete='CASCADE'), primary_key=True)


class newModels:
    """
    New models from luna-faces
    """

    class Face(baseNew):
        """
        Database table model for faces.
        """
        __tablename__ = 'face'

        #: str: face id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        face_id = Column(String(36), primary_key=True)

        #: str: attributes id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        attributes_id = Column(String(36), index=True, unique=True)

        #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        account_id = Column(String(36), index=True)

        # : str: event id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx", reference to event which created
        # the face
        event_id = Column(String(36), index=True)

        #: str: client info about the face
        user_data = Column(String(128), index=True)

        #: DateTime: date and time of creating face
        create_time = Column(TIMESTAMP, index=True)

        #: DateTime: date and time of last changed of the face
        last_update_time = Column(TIMESTAMP, index=True)

        #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        person_id = Column(String(36))

        #: str: external id of the face, if it has its own mapping in external system
        external_id = Column(String(128), index=True)

        def __repr__(self):
            return '<Faces %r>' % self.face_id

    class Person(baseNew):
        """
        Database table model for persons.
        """
        __tablename__ = 'person'

        #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        person_id = Column(String(36), primary_key=True)

        #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        account_id = Column(String(36), index=True)

        #: str: client info about the face
        user_data = Column(String(128), index=True)

        #: DateTime: date and time of creating face
        create_time = Column(TIMESTAMP, index=True)

        def __repr__(self):
            return '<Persons %r>' % self.person_id

    class List(baseNew):
        """
        Database table model for lists.
        """
        __tablename__ = 'list'

        #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        list_id = Column(String(36), primary_key=True)

        #: str: descriptor id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        account_id = Column(String(36), index=True)

        #: str: client info about the list
        user_data = Column(String(128), index=True)

        #: integer: type of list (persons - 1, faces - 0)
        type = Column(Integer, default=1, index=True)

        #: DateTime: date and time of creating list
        create_time = Column(TIMESTAMP, index=True)

        #: DateTime: date and time of last changed of the list
        last_update_time = Column(TIMESTAMP, index=True)

        def __repr__(self):
            return '<Lists %r>' % self.list_id

    class ListFace(baseNew):
        """
        Database table model for links between faces and lists.
        """
        __tablename__ = 'list_face'

        #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), primary_key=True)

        #: str: face id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        face_id = Column(String(36), ForeignKey('face.face_id', ondelete='CASCADE'), primary_key=True)

        #: str: reference to person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        person_id = Column(String(36), index=True)

        #: DateTime: date and time of last attach/detach face to list
        last_update_time = Column(TIMESTAMP, index=True)

        #: int: number of link face to list
        link_key = Column(Integer, LINK_SEQUENCE)

        def __repr__(self):
            return '<listface_list_id %r>' % self.list_id

    class ListPerson(baseNew):
        """
        Database table model for links between persons and lists.
        """
        __tablename__ = 'list_person'

        #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), primary_key=True)

        #: str: person id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        person_id = Column(String(36), ForeignKey('person.person_id', ondelete='CASCADE'), primary_key=True)

        def __repr__(self):
            return '<listperson_list_id %r>' % self.list_id

    class UnlinkAttributesLog(baseNew):
        """
        Database table model for history attach and detach attributes to lists.
        """
        __tablename__ = 'unlink_attributes_log'

        #: str: list id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        list_id = Column(String(36), ForeignKey('list.list_id', ondelete='CASCADE'), index=True)

        #: str: attributes id, uuid4 in format "xxxxxxxx-xxxx-4xxx-{8-9}xx-xxxxxxxxxxxx"
        attributes_id = Column(String(36), index=True)

        #: int: number of link face to list
        link_key = Column(Integer, index=True, unique=True)

        #: int: number of unlink face to list
        unlink_key = Column(Integer, UNLINK_SEQUENCE, primary_key=True)

        #: DateTime: date and time of detach attributes from list
        update_time = Column(TIMESTAMP, server_default=func.now(), index=True)


class newAccModels:
    """
    New models of Account and AccountToken tables
    """
    class Account(baseAccNew):
        """
        Database table model for account.
        """
        __tablename__ = 'account'

        #: uuid4:  account id.
        account_id = Column(String(36), primary_key=True)

        #: bool: account status (blocked or not).
        active = Column(Boolean)

        #: str:  hash from account password. Encryption algorithm is pbkdf2_sha256 from passlib.
        password = Column(String(128))

        #: str: account email.
        email = Column(String(64), unique=True)

        #: str: organization name account represents.
        organization_name = Column(String(128))

        def fillAccount(self, tup) -> baseAccNew:
            """
            Fill account data from array of elements

            :param tup: array with elements (id, active status, password, e-mail, organization name).
            :return: self
            """

            self.account_id = tup[0]
            self.active = tup[1]
            self.password = tup[2]
            self.email = tup[3]
            self.organization_name = tup[4]
            return self

        def __repr__(self):
            return '<Account %r>' % self.account_id

    class AccountToken(baseAccNew):
        """
        Token table.
        """
        __tablename__ = 'account_token'

        #: uuid4: token id
        token_id = Column(String(36), primary_key=True)

        #: uuid4: account id, token is linked to
        account_id = Column(String(36), ForeignKey('account.account_id', ondelete='CASCADE'))

        #: str: string with token data
        token_info = Column(String(128))

        def __repr__(self):
            return '<Accounttoken %r>' % self.token_id
