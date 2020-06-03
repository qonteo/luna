import os

from configs.config import SQLALCHEMY_DATABASE_URI

basedir = os.path.abspath(os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api_db import models


def dump_emails(dst, uri):
    engine = create_engine(uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    query = session.query(models.Account)
    listAccounts = query.filter().all()
    f = open(dst, 'w')
    for account in listAccounts:
        try:
            f.write(account.organization_name + "; " + account.email + ";\n")
        except Exception as e:
            print(str(e))
    f.close()



dump_emails("./emails_luna2.csv", SQLALCHEMY_DATABASE_URI)