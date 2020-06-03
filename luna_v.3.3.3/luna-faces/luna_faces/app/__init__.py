import sys
from logbook import StreamHandler

StreamHandler(sys.stdout).push_application()