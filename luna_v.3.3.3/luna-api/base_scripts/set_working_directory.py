import os
import sys


def setWorkingDirectory():
    """
    Set working directory to "luna_api".
    """
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "luna_api")))

    os.chdir(os.path.join(os.path.dirname(__file__)))
