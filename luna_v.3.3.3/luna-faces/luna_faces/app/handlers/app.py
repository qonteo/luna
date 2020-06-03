from tornado import web

from app.handlers.attributes_handler import AttributesHandler
from app.handlers.error_handler import ErrorHandler404
from app.handlers.face_handler import FaceHandler
from app.handlers.face_linker_handler import FaceToPersonLinkerHandler
from app.handlers.faces_handler import FacesHandler
from app.handlers.faces_attributes_handler import FaceAttributesHandler, FacesAttributesHandler
from app.handlers.gc_handler import GCHandler
from app.handlers.unlink_history_handler import UnlinkHistoryHandler
from app.handlers.linker_handler import LinkerHandler
from app.handlers.list_attributes_handler import ListDescriptorsHandler, ListDeletionsHandler
from app.handlers.list_handler import ListHandler
from app.handlers.lists_handler import ListsHandler
from app.handlers.person_handler import PersonHandler
from app.handlers.persons_handler import PersonsHandler
from app.handlers.persons_attributes_handler import PersonAttributesHandler, PersonsAttributesHandler
from app.handlers.version_handler import VersionHandler
from app.version import VERSION
from crutches_on_wheels.utils.regexps import UUID4_REGEXP_STR as UUID4_REGEXP
from crutches_on_wheels.utils.log import Logger
from configs.config import APP_NAME, LOG_LEVEL, STORAGE_TIME, FOLDER_WITH_LOGS


Logger.initiate(APP_NAME, LOG_LEVEL, STORAGE_TIME, FOLDER_WITH_LOGS)
logger = Logger()  # : logger for debug printing, in standard mode

settings = {}
API = VERSION["Version"]["api"]
application = web.Application([
    (r"/version", VersionHandler),
    (r"/{}/gc".format(API), GCHandler),
    (r"/{}/faces".format(API), FacesHandler),
    (r"/{}/faces/attributes".format(API), FacesAttributesHandler),
    (r"/{}/faces/(?P<faceId>{})".format(API, UUID4_REGEXP), FaceHandler),
    (r"/{}/faces/(?P<faceId>{})/attributes".format(API, UUID4_REGEXP), FaceAttributesHandler),
    (r"/{}/persons".format(API), PersonsHandler),
    (r"/{}/persons/attributes".format(API), PersonsAttributesHandler),
    (r"/{}/persons/(?P<personId>{})".format(API, UUID4_REGEXP), PersonHandler),
    (r"/{}/persons/(?P<personId>{})/attributes".format(API, UUID4_REGEXP), PersonAttributesHandler),
    (r"/{}/lists".format(API), ListsHandler),
    (r"/{}/lists/(?P<listId>{})".format(API, UUID4_REGEXP), ListHandler),
    (r"/{}/lists/(?P<listId>{})/deletions".format(API, UUID4_REGEXP), ListDeletionsHandler),
    (r"/{}/lists/(?P<listId>{})/attributes".format(API, UUID4_REGEXP), ListDescriptorsHandler),
    (r"/{}/linker".format(API), LinkerHandler),
    (r"/{}/linker/unlink_history".format(API), UnlinkHistoryHandler),
    (r"/{}/facelinker".format(API), FaceToPersonLinkerHandler),
    (r"/{}/attributes".format(API), AttributesHandler)
], default_handler_class = ErrorHandler404, **{}, **settings)
