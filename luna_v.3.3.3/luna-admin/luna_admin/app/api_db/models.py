# -*- coding: utf-8 -*-
"""
This module describes api database structure
"""

from app.api_db import metadata
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Account(Base):
    """
    Database table model for account.
    """
    __tablename__ = 'account'
    Base.metadata = metadata

    #: uuid4:  account id.
    account_id = Column(String, primary_key=True, unique=True)

    #: bool: account status (blocked or not).
    active = Column(Boolean)

    #: str:  hash from account password. Encryption algorithm is pbkdf2_sha256 from passlib.
    password = Column(String(128))

    #: str: account email.
    email = Column(String(64), unique=True)

    #: str: organization name account represents.
    organization_name = Column(String(128))

    def __repr__(self):
        return '<account_account_id %r>' % self.account_id


class AccountToken(Base):
    """
    Token table.
    """
    __tablename__ = 'account_token'
    Base.metadata = metadata

    #: uuid4: token id
    token_id = Column(String, primary_key=True, unique=True)

    #: uuid4: account id, token is linked to
    account_id = Column(String, ForeignKey('account.account_id', ondelete='CASCADE'))

    #: str: string with token data
    token_info = Column(String(128))

    def __repr__(self):
        return '<account_token_token_id %r>' % self.token_id
