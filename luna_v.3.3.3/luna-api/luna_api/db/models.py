# -*- coding: utf-8 -*-
"""
This module describes database structure
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from . import metadata

Base = declarative_base()


class Account(Base):
    """
    Database table model for account. 
    """
    __tablename__ = 'account'
    Base.metadata = metadata

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

    def fillAccount(self, tup) -> Base:
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


class AccountToken(Base):
    """
    Token table.
    """

    __tablename__ = 'account_token'
    Base.metadata = metadata

    #: uuid4: token id
    token_id = Column(String(36), primary_key=True)

    #: uuid4: account id, token is linked to
    account_id = Column(String(36), ForeignKey('account.account_id', ondelete='CASCADE'))

    #: str: string with token data
    token_info = Column(String(128))

    def __repr__(self):
        return '<Accounttoken %r>' % self.token_id
