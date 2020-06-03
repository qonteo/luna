from db.context import DBContext
from app.check_connection import logger


def checkTasksStatus() -> None:
    """
    Set 'failed' status to tasks with 'null' status after statring service
    """
    context = DBContext(logger)
    context.updateTasksNullStatus()
