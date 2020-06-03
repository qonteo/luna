# -*- coding: utf-8 -*-
"""
Скрипт для изменения строчки пароля на его hash. 
Предназначен для миграции с версии 0.1.8 до более новых
"""
from set_working_directory import setWorkingDirectory

setWorkingDirectory()

from passlib.hash import pbkdf2_sha256
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from configs.config import SQLALCHEMY_DATABASE_URI
from db import models


def prinPsw(uri):
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(models.Account)
    accounts = query.filter().all()
    for account in accounts:
        print(account.password)


def resetPswToHash(uri):
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(models.Account)
    accounts = query.filter().all()
    for account in accounts:
        try:
            pwdHash = pbkdf2_sha256.hash(account.password)
            account.password = pwdHash
            session.flush()


        except Exception as e:
            print(str(e))
    session.commit()


resetPswToHash(SQLALCHEMY_DATABASE_URI)
print("Success reset password")
