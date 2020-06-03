import tornado
from tornado import web
from app.handlers.fsm_handlers_handler import FSMHandlerHandler, FSMHandlersHandler
from app.handlers.receiver_handler import ReceiverHandler
from app.handlers.reporter_handler import ReporterHandler, ReporterStaticHandler
from app.handlers.version_handler import VersionHandler
from app.handlers.websocket_handler import EventWebSocketHandler, GroupWebSocketHandler
from app.handlers.static_header import EventImgStaticHandler
from app.handlers.events_handler import EventHandler, EventsHandler, EventsStatsHandler
from app.handlers.groups_handler import GroupHandler, GroupsHandler, GroupsStatsHandler
from app.handlers.error_handler import ErrorHandler404
from app.handlers.luna_proxy_handler import LunaProxyHandler
from app.handlers.top_n_nandler import ProbabilityTopNHandler
from app.handlers.linker_handler import LinkerHandler
from app.handlers.clusterization_handler import ClusterizationHandler
from app.handlers.cross_matcher_handler import CrossMatcherHandler
from app.handlers.task_in_progress_handler import TaskInProgressHandler, TasksInProgressHandler
from app.handlers.done_tasks_handler import DoneTaskHandler, DoneTasksHandler
from app.common_objects import API_VERSION

settings = {}

UUID4_REGEXP = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
INT_REGEXP = "[0-9]+"

application = tornado.web.Application([
    (r"/api/{}/handlers".format(API_VERSION), FSMHandlersHandler),
    (r"/luna_api/.*", LunaProxyHandler),
    (r"/api/{}/handlers/(?P<handlerId>{})".format(API_VERSION, UUID4_REGEXP), FSMHandlerHandler),
    (r"/api/{}/events".format(API_VERSION), EventsHandler),
    (r"/api/{}/events/stats".format(API_VERSION), EventsStatsHandler),
    (r"/api/{}/events/(?P<eventId>{})".format(API_VERSION, UUID4_REGEXP), EventHandler),
    (r"/api/{}/events_groups".format(API_VERSION), GroupsHandler),
    (r"/api/{}/events_groups/(?P<groupId>{})".format(API_VERSION, UUID4_REGEXP), GroupHandler),
    (r"/api/{}/events_groups/stats".format(API_VERSION), GroupsStatsHandler),
    (r"/api/{}/receivers/(?P<handlerId>{})".format(API_VERSION, UUID4_REGEXP), ReceiverHandler),
    (r"/api/{}/ws/(?P<handlerId>{})/events".format(API_VERSION, UUID4_REGEXP), EventWebSocketHandler),
    (r"/api/{}/ws/(?P<handlerId>{})/events_groups".format(API_VERSION, UUID4_REGEXP), GroupWebSocketHandler),
    (r"/api/{}/analytics/probability_calculator".format(API_VERSION), ProbabilityTopNHandler),
    (r"/api/{}/analytics/clusterizer".format(API_VERSION), ClusterizationHandler),
    (r"/api/{}/analytics/cross_matcher".format(API_VERSION), CrossMatcherHandler),
    (r"/api/{}/analytics/tools/linker".format(API_VERSION), LinkerHandler),
    (r"/api/{}/analytics/tools/reporter".format(API_VERSION), ReporterHandler),
    (r"/api/{}/analytics/tasks".format(API_VERSION), DoneTasksHandler),
    (r"/api/{}/analytics/tasks/(?P<taskId>{})".format(API_VERSION, INT_REGEXP), DoneTaskHandler),
    (r"/api/{}/tasks".format(API_VERSION), TasksInProgressHandler),
    (r"/api/{}/tasks/(?P<taskId>{})".format(API_VERSION, INT_REGEXP), TaskInProgressHandler),
    (r'/storage/events/({})'.format(UUID4_REGEXP), EventImgStaticHandler, {'path': "./storage/events"}),
    (r"/api/{}/reports/({})".format(API_VERSION, INT_REGEXP), ReporterStaticHandler, {'path': "./storage/reports"}),
    (r"/version", VersionHandler)

], default_handler_class = ErrorHandler404, **settings)
