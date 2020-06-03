# -*- coding: utf-8 -*-
"""Module for parsing command line arguments

Module provides a function for parsing input command line.
"""
from tornado.options import OptionParser
import sys


def getOptionsParser():
    """
    Get the start option.

    Note:
        In command line you can set two arguments *port, config*. *port* argument is responsible for port, on which
        service listens, *config* argument is responsible for path to config file.

    Returns:
        OptionParser: option parser
    """
    op = OptionParser()
    op.define('port', default=5060, help='listener port', type=int)
    op.define('config', default="./configs/config.conf", help='config file path', type=str)
    if sys.argv[0].find("sphinx") < 0:  #: fix sphinx build
        op.parse_command_line()
    return op
