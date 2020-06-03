#!/bin/python3
import sys, os
from alembic.config import Config
from alembic import command

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "luna_index_manager")))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "luna_index_manager")))

from db.models import metadata

metadata.create_all()

os.chdir(os.path.pardir)
alembic_cfg = Config("alembic.ini")
command.stamp(alembic_cfg, "head")
