from tornado import web

from app.rest_handlers.account_handler import AccountInfoHandler, AccountStatsHandler
from app.rest_handlers.create_person_handler import PersonCreateHandler
from app.rest_handlers.descriptor_handler import DescriptorHandler
from app.rest_handlers.error_handler import ErrorHandler404
from app.rest_handlers.linker_handler import LinkerHandler
from app.rest_handlers.lists_handler import ListHandler, ListOfObjectHandler
from app.rest_handlers.matcher_handler import MatcherIdentifyHandler, MatcherVerifyHandler, MatcherSearchHandler, \
    MatcherDescriptorHandler
from app.rest_handlers.person_handler import PersonHandler
from app.rest_handlers.person_link_descriptor_handler import PersonLinkDescriptorHandler
from app.rest_handlers.person_link_list_handler import PersonLinkListHandler
from app.rest_handlers.photo_handler import PhotoHandler, GetterPhotoHandler
from app.rest_handlers.photo_link_photo_to_list_handler import PhotoLinkListHandler
from app.rest_handlers.registration_handler import RegistrationHandler
from app.rest_handlers.storage_handlers import LoginHandler
from app.rest_handlers.token_handler import TokenHandler
from app.rest_handlers.tokens_handler import TokensHandler
from app.rest_handlers.version_handler import VersionHandler
from crutches_on_wheels.utils.regexps import UUID4_REGEXP_STR as UUID4_REGEXP

settings = {}
API_VERSION = "4"

application = web.Application([
    (r"/{}/matching/identify".format(API_VERSION), MatcherIdentifyHandler),
    (r"/{}/matching/verify".format(API_VERSION), MatcherVerifyHandler),
    (r"/{}/matching/search".format(API_VERSION), MatcherSearchHandler),
    (r"/{}/matching/match".format(API_VERSION), MatcherDescriptorHandler),

    (r"/{}/storage/descriptors".format(API_VERSION), PhotoHandler),
    (r"/{}/storage/descriptors/(?P<descriptor_id>{})".format(API_VERSION, UUID4_REGEXP),
     DescriptorHandler),
    (r"/{}/storage/descriptors/(?P<photo_id>{})/linked_lists".format(API_VERSION, UUID4_REGEXP),
     PhotoLinkListHandler),

    (r"/{}/storage/portraits/(?P<photo_id>{})(?P<thumbnail>_[0-9]+)?".format(API_VERSION, UUID4_REGEXP),
     GetterPhotoHandler),

    (r"/{}/storage/persons".format(API_VERSION), PersonCreateHandler),
    (r"/{}/storage/persons/(?P<person_id>{})".format(API_VERSION, UUID4_REGEXP), PersonHandler),
    (r"/{}/storage/persons/(?P<person_id>{})/linked_descriptors".format(API_VERSION, UUID4_REGEXP),
     PersonLinkDescriptorHandler),
    (r"/{}/storage/persons/(?P<person_id>{})/linked_lists".format(API_VERSION, UUID4_REGEXP), PersonLinkListHandler),

    (r"/{}/account".format(API_VERSION), AccountInfoHandler),

    (r"/{}/accounts".format(API_VERSION), RegistrationHandler),
    (r"/{}/account/statistics".format(API_VERSION), AccountStatsHandler),
    (r"/{}/account/tokens".format(API_VERSION), TokensHandler),
    (r"/{}/account/tokens/(?P<token_id>{})".format(API_VERSION, UUID4_REGEXP), TokenHandler),

    (r"/{}/storage/lists".format(API_VERSION), ListHandler),
    (r"/{}/storage/lists/(?P<listId>{})".format(API_VERSION, UUID4_REGEXP), ListOfObjectHandler),
    (r"/{}/storage/linker".format(API_VERSION), LinkerHandler),

    (r'/version', VersionHandler),

    (r"/{}/login".format(API_VERSION), LoginHandler)

], default_handler_class = ErrorHandler404, **settings)
