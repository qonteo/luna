from tornado.options import OptionParser
import os
import sys

def getOptionsParser():
    """
    Get the start option.

    note:  In command line you can set two arguments *workers, port*. *workers* argument is responsible for
    number of launched workers, *port* argument is responsible for port, on which service listens.

    :return: parsed options
    """
    op = OptionParser()
    op.define('events_port', default = 5100, help = 'listener port', type = int)
    op.define('analytics_port', default = 5101, help = 'listener port', type = int)
    op.define('config', default = "./configs/config.conf", help = 'path to config', type = str)
    if not ~sys.argv[0].find("sphinx"):
        # if no sphinx found
        op.parse_command_line()
    return op
