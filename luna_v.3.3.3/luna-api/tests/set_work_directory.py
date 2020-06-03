import sys
import os.path


def setWorkingDirectory():
    sys.path.append(
        os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

    os.chdir(os.path.join(os.path.dirname(__file__)))