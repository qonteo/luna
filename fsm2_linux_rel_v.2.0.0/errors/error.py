# -*- coding: utf-8 -*-
from collections import namedtuple
import inspect

_ = namedtuple("ErrorInfo", ['code', 'eng'])


class ErrorInfo:
    """
    Nested error class.

    Attributes:
        info (_): named tuple, use like:
            tuple: obj[0], obj[1]
            or structure: obj.code, obj.eng
    """
    def __init__(self, code, description):
        self.info = _(code, description)

    def getErrorDescription(self):
        """
        Get error description

        :return: description
        """
        return self.info.eng

    def getErrorCode(self):
        """
        Get error code

        :return: code
        """
        return self.info.code


class NetworkError:
    """
    Network error container.
    """
    ESConnectionTimeout = ErrorInfo(11001, 'Connection timeout to ES')
    ESRequestTimeout = ErrorInfo(11002, 'Request timeout to ES')
    LunaConnectionTimeout = ErrorInfo(11003, 'Connection timeout to Luna API')
    LunaRequestTimeout = ErrorInfo(11004, 'Request timeout to Luna API')
    LunaMatchError = ErrorInfo(11005, 'Search request failed,  error_code: {}, detail: {}')
    LunaCreatePersonError = ErrorInfo(11006, 'Search request failed,  error_code: {}, detail: {}')
    LunaRequestError = ErrorInfo(11007, '{} request failed.  error_code: {}, detail: {}')


class RESTAPIError:
    """
    Rest API error container.
    """
    BadFormatUUID = ErrorInfo(12001, 'Object in  query is not UUID4, format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx')
    RequestNotContainsJson = ErrorInfo(12002, 'Request does not contain json')
    FieldNotInJSON = ErrorInfo(12003, "Field '{}' not found in json")
    BadTypeOfFieldInJSON = ErrorInfo(12004, "Field '{}' must be {}")
    EmptyJson = ErrorInfo(12005, 'Request contain empty json')
    BadQueryParam = ErrorInfo(12012, "Bad query parameter '{}'")
    QueryParameterNotFound = ErrorInfo(12014, "Required parameter '{}' not found")
    ManyFaces = ErrorInfo(11012, "Too many faces found")
    RequiredQueryParameterNotFound = ErrorInfo(12016, "No one  parameters '{}' not found")
    BadContentType = ErrorInfo(12017, "Bad content type")
    UnsupportedQueryParm = ErrorInfo(12018, "Unsupported param '{}'")
    BadInputJson = ErrorInfo(12019, "Failed to validate input json. Path: '{}',  message: '{}'")
    ConvertBase64Error = ErrorInfo(12023, "Failed convert data from base64 to bytes")
    ConvertImageToJPGError = ErrorInfo(12024, "Failed convert bytes to jpg")
    PageNotFoundError = ErrorInfo(12021, "Page not found")
    MethodNotAllowed = ErrorInfo(12022, "Method not allowed")
    MultipleFacesError = ErrorInfo(12023, "Multiple faces")
    GroupByTooLow = ErrorInfo(12024, "Group step '{}' is too low")
    Forbidden = ErrorInfo(12025, '{} is disabled according to the current configuration')


class ElasticError:
    """
    Elasticsearch error container.
    """
    ElasticNotFound = ErrorInfo(13001, 'Resource not found')
    EventNotFound = ErrorInfo(13002, 'No event found by id')
    HandlerNotFound = ErrorInfo(13003, 'No handler found by id')
    GroupNotFound = ErrorInfo(13004, 'No group found by id')

    ElasticMalformedRequest = ErrorInfo(13005, 'Wrong internal request format to Elasticsearch')
    ElasticServiceUnavailable = ErrorInfo(13006, 'Cannot reach Elasticsearch')
    ElasticInternal = ErrorInfo(13007, 'Internal Elasticsearch error')
    ElasticTimeout = ErrorInfo(13008, 'Timeout during request to Elastic')
    ElasticRequest = ErrorInfo(13009, 'Failed create or send request to Elastic')
    TaskNotFound = ErrorInfo(13010, 'No task found by id')
    TaskNotFoundCorrespondingType = ErrorInfo(13011, 'No task found by id and type, expected type "{}"')

    TooManyEvents = ErrorInfo(13012, 'Cannot get all events')
    TooManyGroups = ErrorInfo(13013, 'Cannot get all groups')


class FSMErrors:
    """
    Facestreammanager2 error container.
    """
    HandlerStepError = ErrorInfo(14001, 'Failed step {}')


class TaskError:
    """
    Tasks error container.
    """
    UnknownTaskType = ErrorInfo(15000, 'Unknown type of task')
    SendTaskToExecuteError = ErrorInfo(15001, 'Failed to send task to execute')
    TaskCanceled = ErrorInfo(15002, 'Task cancelled')
    UnsupportedTaskType = ErrorInfo(15003, 'Unsupported type of task for this resource')
    TaskFiltersNotFoundListId = ErrorInfo(15004, 'Type of objects in task "luna_list" but "list_id" '
                                                 'in filters not found')
    UncaughtTaskException = ErrorInfo(15005, 'Unknown error in processing task')
    NotImplementedError = ErrorInfo(15006, 'Result generator is not implemented yet')
    InconsistentInputDataError = ErrorInfo(15007, 'Inconsistent input data found: "{}"')
    NoObjectsFound = ErrorInfo(15008, 'No objects for task found')

class InternalError:
    """
    Internal error container.
    """
    RequestInternalServerError = ErrorInfo(16009, 'Internal server error')
    ConvertLunaJsonError = ErrorInfo(16010, 'Conversion json error')
    InternalServerError = ErrorInfo(16006, 'Internal server error')


class ClusterizerError:
    """
    Clusterization task error container.
    """
    ClusterErrorObjectType = (17000, 'Unsupported  object type: {}')
    FailedToGetObjectsFromLunaList = (17000, 'Failed to get all objects from luna list {}')


class LinkerError:
    """
    Linker task error container.
    """
    LinkDescriptorError = ErrorInfo(18000, 'Cannot link descriptor {} to list {}')
    LinkPersonError = ErrorInfo(18001, 'Cannot link person {} to list {}')
    LinkDescriptorsError = ErrorInfo(18002, 'Cannot link descriptors')
    LinkPersonsError = ErrorInfo(18003, 'Cannot link persons')
    LinkDescriptorToPersonError = ErrorInfo(18004, 'Cannot link descriptor {} to person {}')


class Error(RESTAPIError, NetworkError, ElasticError, InternalError, FSMErrors, TaskError, LinkerError, ClusterizerError):
    """
    All errors container.
    """
    Success = ErrorInfo(0, 'Success')
    UnknownError = ErrorInfo(1, 'Unknown error')
    IncompatibleError = ErrorInfo(2, 'Incompatible data, {}')

    @staticmethod
    def getErrorByErrorCode(errorCode):
        """
        Get an error by the error code.

        :param errorCode: the error code
        :return: nested error
        """
        members = inspect.getmembers(Error)
        for member in members:
            if type(member[1]).__name__ == "ErrorInfo":
                if member[1].errorCode == errorCode:
                    return getattr(Error, member[0])
        return Error.UnknownError

    @staticmethod
    def generateError(error, msg):
        """
        Change error description in known error.

        :param error: error to get error code from
        :param msg: new error description
        :return: new error
        """
        return ErrorInfo(error.getErrorCode(), msg)

    @staticmethod
    def generateLunaError(requestDescription, lunaReply) -> ErrorInfo:
        """
        Generate Luna API request error from Luna API response.

        :param requestDescription: the failed request description
        :param lunaReply: failed request response
        :return: generated error
        """
        return ErrorInfo(Error.LunaRequestError.getErrorCode(),
                         Error.LunaRequestError.getErrorDescription().format(requestDescription,
                                                                             lunaReply["error_code"],
                                                                             lunaReply["detail"]))


class Result:
    def __init__(self, error: ErrorInfo, value: object):
        self.error = error
        self.value = value

    def __repr__(self):
        return '<Result> {}: {}'.format(self.description, self.value)

    @property
    def description(self):
        return self.error.getErrorDescription()

    @property
    def errorCode(self):
        return self.error.getErrorCode()

    @property
    def success(self):
        return self.error == Error.Success

    @property
    def fail(self):
        return self.error != Error.Success
