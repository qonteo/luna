#!/bin/python3
import sys, os
from alembic.config import Config
from alembic import command


basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "luna_admin")))

from app.admin_db import metadata
from app.admin_db.db_context import createAdmin


metadata.create_all()

createAdmin()

os.chdir(os.path.pardir)
alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")
