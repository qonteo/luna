from tornado.options import OptionParser
import sys


def getOptionsParser():
    """
    Get the start option.

    note:  In command line you can set two arguments *workers, port*. *workers* argument is responsible for\
    number of launched workers, *port* argument is responsible for port, on which service listens.

    :return: parsed options
    """
    op = OptionParser()
    op.define('port', default = 5030, help = 'listener port', type = int)
    op.define('workers', default = 1, help = 'worker count', type = int)
    op.define('config', default = "./configs/config.conf", help = 'worker count', type = str)
    if sys.argv[0].find("sphinx") < 0:  #: fix sphinx build
        op.parse_command_line()
    return op
