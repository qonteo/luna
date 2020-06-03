from tests.system_tests.config import FSM2_URL, FSM2_API_VERSION
import requests
import ujson as json
from enum import Enum


class Reply:
    json = {}
    statusCode = 0
    headers = {}

    def __repr__(self):
        return "<Reply> {}: {}".format(self.statusCode, self.json)


class RequestMethod(Enum):
    GET = 0
    POST = 1
    PUT = 2
    DELETE = 3
    PATCH = 4

    @staticmethod
    def getRequestMethod(method):
        if method == RequestMethod.POST:
            return requests.post
        if method == RequestMethod.GET:
            return requests.get
        if method == RequestMethod.PUT:
            return requests.put
        if method == RequestMethod.PATCH:
            return requests.patch
        if method == RequestMethod.DELETE:
            return requests.delete


def createPayloadImg(pathToPhoto):
    with open(pathToPhoto, "rb") as f:
        imgBytes = f.read()
    return imgBytes


def makeRequest(url, method, body = None, headers = None, queries = None):
    if body is not None:
        if headers['Content-Type'] == "application/json":
            payload = json.dumps(body, ensure_ascii = False)
        else:
            payload = body
    else:
        payload = body
    reply = RequestMethod.getRequestMethod(method)(url, headers = headers, data = payload, params = queries,
                                                   allow_redirects = False)

    if 200 <= reply.status_code < 300:
        if method not in (RequestMethod.PATCH, RequestMethod.DELETE):
            if reply.headers['Content-Type'] != "application/json":
                print(url)
                raise ValueError("bad content type")
        else:
            if 'Content-Type' in reply.headers:
                print(url)
                raise ValueError("bad content type")

    repText = reply.text
    if len(repText) > 0:
        repJson = json.loads(repText)
    else:
        repJson = {}
    res = Reply()
    res.json = repJson
    res.statusCode = reply.status_code
    res.headers = reply.headers
    return res


def createHandler(handler):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/handlers".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.POST, headers = headers,
                       body = handler)


def getHandlers(params=None):
    return makeRequest("{}/api/{}/handlers".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.GET, queries=params or {})


def getHandlerById(handlerId):
    return makeRequest("{}/api/{}/handlers/{}".format(FSM2_URL, FSM2_API_VERSION, handlerId), RequestMethod.GET)


def getHandlersByName(name):
    pass


def deleteHandler(handlerId):
    return makeRequest("{}/api/{}/handlers/{}".format(FSM2_URL, FSM2_API_VERSION, handlerId), RequestMethod.DELETE)


def putHandler(handler):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/handlers/{}".format(FSM2_URL, FSM2_API_VERSION, handler["id"]), RequestMethod.PUT,
                       body = handler,
                       headers = headers)


def emitEvent(handlerId, imgPath, queryParams = None):
    imgBody = createPayloadImg(imgPath)
    headers = {'Content-Type': "image/jpeg"}
    if queryParams is None:
        queryParams_ = {}
    else:
        queryParams_ = queryParams
    return makeRequest("{}/api/{}/receivers/{}".format(FSM2_URL, FSM2_API_VERSION, handlerId), RequestMethod.POST,
                       body = imgBody,
                       headers = headers, queries = queryParams_)


def getEvent(eventId):
    return makeRequest("{}/api/{}/events/{}".format(FSM2_URL, FSM2_API_VERSION, eventId), RequestMethod.GET)


def getImgOfEvent(eventId):
    return makeRequest("{}/storage/events/{}".format(FSM2_URL, FSM2_API_VERSION, eventId), RequestMethod.GET)


def searchEvents(filters):
    return makeRequest("{}/api/{}/events".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.GET, queries = filters)


def statsEvents(filters):
    return makeRequest("{}/api/{}/events/stats".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.GET,
                       queries = filters)


def statsGroups(filters):
    return makeRequest("{}/api/{}/events_groups/stats".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.GET,
                       queries = filters)


def searchGroups(filters):
    return makeRequest("{}/api/{}/events_groups".format(FSM2_URL, FSM2_API_VERSION), RequestMethod.GET,
                       queries = filters)


def getGroup(groupId):
    return makeRequest("{}/api/{}/events_groups/{}".format(FSM2_URL, FSM2_API_VERSION, groupId), RequestMethod.GET)


def createTaskHitTopN(params):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/analytics/probability_calculator".format(FSM2_URL, FSM2_API_VERSION),
                       RequestMethod.POST, body = params, headers= headers)


def createTaskLinker(params):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/analytics/tools/linker".format(FSM2_URL, FSM2_API_VERSION),
                       RequestMethod.POST, body = params, headers= headers)


def createTaskCrossMatcher(params):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/analytics/cross_matcher".format(FSM2_URL, FSM2_API_VERSION),
                       RequestMethod.POST, body = params, headers= headers)


def createTaskReporter(params):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/analytics/tools/reporter".format(FSM2_URL, FSM2_API_VERSION),
                       RequestMethod.POST, body = params, headers= headers)


def createTaskClusterization(params):
    headers = {'Content-Type': "application/json"}
    return makeRequest("{}/api/{}/analytics/clusterizer".format(FSM2_URL, FSM2_API_VERSION),
                       RequestMethod.POST, body = params, headers= headers)


def getDoneTask(taskId):
    return makeRequest("{}/api/{}/analytics/tasks/{}".format(FSM2_URL, FSM2_API_VERSION, taskId),
                       RequestMethod.GET)


def getReport(taskId):
    return requests.get("{}/api/{}/reports/{}".format(FSM2_URL, FSM2_API_VERSION, taskId))


def getTaskInProgress(taskId):
    return makeRequest("{}/api/{}/tasks/{}".format(FSM2_URL, FSM2_API_VERSION, taskId),
                       RequestMethod.GET)


def cancelTaskInProgress(taskId):
    return makeRequest("{}/api/{}/tasks/{}".format(FSM2_URL, FSM2_API_VERSION, taskId),
                       RequestMethod.DELETE)

def getVersion():
    return makeRequest("{}/version".format(FSM2_URL), RequestMethod.GET)
