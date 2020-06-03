"""
Module realize  parsing command line arguments.
"""
from tornado.options import OptionParser
import sys


def getOptionsParser() -> OptionParser:
    """
    Get the start option.

    Note:
        In command line you can set two arguments *workers, port*. *workers* argument is responsible for
        number of launched workers, *port* argument is responsible for port, on which service listens.

    Returns:
         parsed options
    """
    op = OptionParser()
    op.define('service_type', help='"admin_backend" or "admin_task"', type=str)
    op.define('back_port', default=5010, help='listener port for admin backend service', type=int)
    op.define('task_port', default=5011, help='listener port for service of admin long task', type=int)
    op.define('config', default="./configs/config.conf", help='path to config', type=str)
    op.define('workers', default=1, help='worker count', type=int)
    if sys.argv[0].find("sphinx") < 0:  #: fix sphinx build
        op.parse_command_line()
    return op
