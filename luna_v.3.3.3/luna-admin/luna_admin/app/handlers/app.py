"""
Module realize tornado application
Attributes:
    application(web.Application):  tornado application for api.
"""
import os
from tornado import web

from app.handlers.account_handler import AccountHandler
from app.handlers.account_lists_handler import AccountListsHandler, AccountListHandler
from app.handlers.account_tokens_handler import AccountTokensHandler
from app.handlers.accounts_handler import AccountsHandler
from app.handlers.base_handler import LoginHandler
from app.handlers.config_handler import ConfigHandler
from app.handlers.error_handler import ErrorHandler404
from app.handlers.gc_handler import GCHandler, TasksHandler, TaskHandler, TaskErrorsHandler
from app.handlers.grafana_handler import GrafanaHandler
from app.handlers.persons_handler import PersonsHandler, PersonHandler
from app.handlers.realtime_statistics import RealtimeStatisticsHandler
from app.handlers.reextract_handler import ReExtractHandler
from app.handlers.search import SearchHandler
from app.handlers.template_account_handler import TemplateAccountHandler, TemplateAccountListsHandler, \
    TemplateAccountTokensHandler
from app.handlers.template_accounts_handler import TemplateAccountsHandler
from app.handlers.template_grafana_handler import TemplateGrafanaHandler
from app.handlers.template_login_handler import TemplateLoginHandler
from app.handlers.template_search import TemplateSeacrhHandler
from app.handlers.template_tasks_handler import TemplateTasksViewHandler, TemplateTasksHandler
from app.handlers.template_version_handler import TemplateVersionHandler
from app.handlers.version_handler import VersionHandler
from app.version import VERSION
from crutches_on_wheels.utils.log import Logger
from configs.config import APP_NAME, LOG_LEVEL, LOG_TIME, FOLDER_WITH_LOGS


Logger.initiate(appName=APP_NAME, logLevel=LOG_LEVEL, logTime=LOG_TIME, folderForLog=FOLDER_WITH_LOGS)
logger = Logger()  # : logger for debug printing, in standard mode

dirname = os.path.dirname(__file__)

STATIC_PATH = os.path.join(dirname, 'static')
TEMPLATE_PATH = os.path.join(dirname, 'templates')
settings = {
    "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
    "login_url": "/login",
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}

UUID4_REGEXP = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
INT_REGEXP = "[0-9]+"
API_VERSION = VERSION["Version"]["api"]
application = web.Application([
    (r"/{}/gc".format(API_VERSION), GCHandler),
    (r"/{}/reextract".format(API_VERSION), ReExtractHandler),
    (r"/{}/tasks".format(API_VERSION), TasksHandler),
    (r"/{}/tasks/(?P<taskId>{})".format(API_VERSION, INT_REGEXP), TaskHandler),
    (r"/{}/tasks/(?P<taskId>{})/errors".format(API_VERSION, INT_REGEXP), TaskErrorsHandler),
    (r"/{}/accounts".format(API_VERSION), AccountsHandler),
    (r"/{}/accounts/(?P<account_id>{})".format(API_VERSION, UUID4_REGEXP), AccountHandler),
    (r"/{}/accounts/(?P<account_id>{})/tokens".format(API_VERSION, UUID4_REGEXP), AccountTokensHandler),
    (r"/{}/persons".format(API_VERSION), PersonsHandler),
    (r"/{}/persons/(?P<personId>{})".format(API_VERSION, UUID4_REGEXP), PersonHandler),
    (r"/{}/login".format(API_VERSION).format(API_VERSION), LoginHandler),
    (r"/{}/search".format(API_VERSION), SearchHandler),
    (r"/version", VersionHandler),
    (r"/{}/grafana".format(API_VERSION), GrafanaHandler),
    (r"/{}/realtime_statistics/(?P<series>(?:extract_success|matching_success|errors))".format(API_VERSION),
     RealtimeStatisticsHandler),
    (r"/{}/lists".format(API_VERSION), AccountListsHandler),
    (r"/{}/lists/(?P<listId>{})".format(API_VERSION, UUID4_REGEXP), AccountListHandler),
    (r"/{}/config".format(API_VERSION), ConfigHandler),
    (r"/", TemplateAccountsHandler),
    (r"/accounts", TemplateAccountsHandler),
    (r"/accounts/(?P<accountId>{})".format(UUID4_REGEXP), TemplateAccountHandler),
    (r"/accounts/(?P<accountId>{})/lists".format(UUID4_REGEXP), TemplateAccountListsHandler),
    (r"/accounts/(?P<accountId>{})/tokens".format(UUID4_REGEXP), TemplateAccountTokensHandler),
    (r"/search", TemplateSeacrhHandler),
    (r"/login", TemplateLoginHandler),
    (r"/tasks/view", TemplateTasksViewHandler),
    (r"/tasks", TemplateTasksHandler),
    (r"/version/view", TemplateVersionHandler),
    (r"/grafana/view", TemplateGrafanaHandler)

], default_handler_class=ErrorHandler404, **settings)
