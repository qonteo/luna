"""
Module for creating engine to admin database.

Attributes:
    engine: engine to admin database.
    metadata: metadata for current engine
"""
from sqlalchemy import create_engine, MetaData
from configs.config import LUNA_API_DB_URI


engine = create_engine(LUNA_API_DB_URI)
metadata = MetaData(bind=engine)
