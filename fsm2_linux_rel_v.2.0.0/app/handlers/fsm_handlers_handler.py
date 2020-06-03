import ujson as json

from tornado import web, gen

from app.common_objects import logger
from app.classes.fsm_handlers import Matcherhandler, ExtractorHandler
from app.common_objects import ES_CLIENT as es
from app.handlers.base_handler import BaseHandler, coRequestExeptionWrap
from app.handlers.schemas import CREATE_SEARCH_SCHEMA, CREATE_EXTRACT_SCHEMA, UPDATE_SEARCH_SCHEMA, \
    UPDATE_EXTRACT_SCHEMA
from app.classes.fsm_handlers import HandlerManager
from errors.error import Error, Result


def checkCompatibilityFiltersAndExtractPolicies(inputHandler):
    """
    Validate the estimate_attributes flag in the extract_policy if handler filters use face attributes.
    Validate the search-type handler if handler filters use similarity.

    :param inputHandler: handler dict to validate
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    estimateAttribute = False
    if "extract_policy" in inputHandler:
        if "estimate_attributes" in inputHandler["extract_policy"]:
            estimateAttribute = bool(inputHandler["extract_policy"]["estimate_attributes"])

    pathToError = ""

    def checkAttributePolicy(policy, path, needEstimateAttribute):
        """
        Recursive attributes filters search.

        :param policy: a policy to search in
        :param path: the current policy path in the handler
        :param needEstimateAttribute: shows if estimate_attributes are enabled in the extract policy
        :return: path of an error or None if ok
        """
        if type(policy) == dict:
            for member in policy:
                path += "." + member
                if member in ["gender", "age_range"]:
                    if not needEstimateAttribute:
                        return path

                pathToCompatibility = checkAttributePolicy(policy[member], path, needEstimateAttribute)
                if pathToCompatibility is not None:
                    return pathToCompatibility
            return None
        if type(policy) == list:
            for number, member in enumerate(policy):
                path += "." + str(number)
                pathToCompatibility = checkAttributePolicy(member, path, needEstimateAttribute)
                if pathToCompatibility is not None:
                    return pathToCompatibility
            return None
        return None

    def checkSimilarityPolicy(policy, path, needCalculateSimilarity):
        """
        Recursive similarity_filter search.

        :param policy: a policy to search in
        :param path: the current policy path in the handler
        :param needCalculateSimilarity: shows if similarity can be obtained from search response
        :return: path of an error or None if ok
        """
        if type(policy) == dict:
            for member in policy:
                path += "." + member
                if member in ["similarity_filter"]:
                    if not needCalculateSimilarity:
                        return path

                pathToCompatibility = checkSimilarityPolicy(policy[member], path, needCalculateSimilarity)
                if pathToCompatibility is not None:
                    return pathToCompatibility
            return None
        if type(policy) == list:
            for count, member in enumerate(policy):
                path += "." + str(count)
                pathToCompatibility = checkSimilarityPolicy(member, path, needCalculateSimilarity)
                if pathToCompatibility is not None:
                    return pathToCompatibility
            return None
        return None

    for policy in ["descriptor_policy", "person_policy", "group_policy"]:
        if policy in inputHandler:

            incompatibleError = checkAttributePolicy(inputHandler[policy], pathToError, estimateAttribute)
            if incompatibleError is not None:
                incompatibleError = incompatibleError[1:]
                error = Error.generateError(Error.IncompatibleError, "Attribute is not estimate but there is "
                                                                     "filter which used it, path: {}"
                                                                     "".format(incompatibleError))
                logger.debug("incompatible error, {}".format(incompatibleError))
                return Result(error, incompatibleError)

            if inputHandler["type"] == "extract":
                incompatibleError = checkSimilarityPolicy(inputHandler[policy], pathToError, False)
                if incompatibleError is not None:
                    incompatibleError = incompatibleError[1:]
                    error = Error.generateError(Error.IncompatibleError, "Handler type is 'extractor' but"
                                                                         "there is filter which used similarity, "
                                                                         "path: {}".format(incompatibleError))
                    logger.debug("incompatible error, {}".format(incompatibleError))
                    return Result(error, incompatibleError)

    return Result(Error.Success, 0)


def checkCompatibilityCreatingPerson(inputHandler):
    """
    Check if person is not created both from descriptor and from group descriptors.

    :param inputHandler: handler to validate
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    if "person_policy" not in inputHandler:
        return Result(Error.Success, 0)
    if "grouping_policy" not in inputHandler:
        return Result(Error.Success, 0)
    if "create_person_policy" not in inputHandler["grouping_policy"]:
        return Result(Error.Success, 0)
    if inputHandler["grouping_policy"]["create_person_policy"]["create_person"] == 1 and \
                    inputHandler["person_policy"]["create_person_policy"]["create_person"] == 1:
        error = Error.generateError(Error.IncompatibleError, "can not create a person from the "
                                                             "group and descriptor simultaneously")
        logger.debug(error.getErrorDescription())
        return Result(error, 0)
    return Result(Error.Success, 0)


def checkCompatibilityHandlerPolicies(inputHandler):
    """
    Check policies.
    Check person creation.

    :param inputHandler: handler to validate
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    checkRes = checkCompatibilityFiltersAndExtractPolicies(inputHandler)
    if checkRes.fail:
        return checkRes
    return checkCompatibilityCreatingPerson(inputHandler)


class FSMHandlersHandler(BaseHandler):
    """
    Handlers handler.
    """
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self):
        """
        Search created handler by name with pagination.
        Response status codes:
            200 if search succeed
            400 if parameters are wrong
            500 if internal system error occurred

        :return: None
        """
        try:
            pageSize = max(min(int(self.get_query_argument("page_size", 20)), 100), 1)
        except ValueError:
            return self.error(400, Error.BadQueryParam.getErrorCode(),
                              Error.BadQueryParam.getErrorDescription().format('page_size'))
        try:
            page = max(int(self.get_query_argument("page", 1)), 1)
        except ValueError:
            return self.error(400, Error.BadQueryParam.getErrorCode(),
                              Error.BadQueryParam.getErrorDescription().format('page'))
        name = self.get_query_argument("name", None)

        handlersRes = yield es.getHandlers(pageSize, page, name)
        if handlersRes.fail:
            return self.error(500, handlersRes.error, handlersRes.description)
        self.set_header('Content-Type', 'application/json')
        self.set_status(200)
        self.finish(json.dumps(handlersRes.value, ensure_ascii = False))

    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def post(self):
        """
        Create handler from input json.
        Response status codes:
            201 if handler was created successfully
            400 if json was not validated
            415 if content type is not 'application/json'
            500 if internal system error occurred

        :return: None
        """
        contentType = self.request.headers.get("Content-Type", None)
        if contentType != 'application/json':
            error = Error.BadContentType
            self.error(415, error.getErrorCode(), error.getErrorDescription())
        newHandler = self.loads()
        if newHandler is None:
            return
        if "type" not in newHandler:
            error = Error.FieldNotInJSON
            return self.error(400, error.getErrorCode(), error.getErrorDescription().format("type"))
        if newHandler["type"] not in ["search", "extract"]:
            error = Error.generateError(Error.BadInputJson,
                                        Error.BadInputJson.getErrorDescription().format("type", "'type' must be "
                                                                                                "'search' or 'extract"))
            return self.error(400, error.getErrorCode(), error.getErrorDescription())
        handlerType = newHandler["type"]

        if handlerType == "search":
            if not self.validateJson(newHandler, CREATE_SEARCH_SCHEMA):
                return
            handler = Matcherhandler(**newHandler)
        else:
            if not self.validateJson(newHandler, CREATE_EXTRACT_SCHEMA):
                return
            handler = ExtractorHandler(**newHandler)

        checkCompatibilityRes = checkCompatibilityHandlerPolicies(newHandler)
        if checkCompatibilityRes.fail:
            return self.error(400, checkCompatibilityRes.errorCode, checkCompatibilityRes.description)

        esReply = yield es.putHandler(handler)
        if esReply.fail:
            return self.error(500, esReply.errorCode, esReply.description)
        return self.success(201, {"handler_id": handler.id})


class FSMHandlerHandler(BaseHandler):
    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def get(self, handlerId):
        """
        Get created handler by handler id.
        Response status codes:
            200 if handler was found
            404 if handler was not found
            500 if internal system error occurred

        :param handlerId: handler id
        :return: None
        """
        handlerRes = yield es.getHandler(handlerId)
        if handlerRes.fail:
            if handlerRes.error == Error.HandlerNotFound:
                return self.error(404, handlerRes.errorCode, handlerRes.description)
            return self.error(500, handlerRes.errorCode, handlerRes.description)
        return self.success(200, handlerRes.value)

    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def put(self, handlerId):
        """
        Update created handler.
        Response status codes:
            201 if handler was updated successfully
            400 if input json was not validated
            415 if content type is not 'application/json'
            500 if internal system error occurred

        :param handlerId: handler id
        :return: None
        """
        contentType = self.request.headers.get("Content-Type", None)
        if contentType != 'application/json':
            self.error(415, Error.BadContentType.getErrorCode(), Error.BadContentType.getErrorDescription())
        updateHandler = self.loads()
        if updateHandler is None:
            return

        handlerType = updateHandler["type"]
        if handlerType == "search":
            if not self.validateJson(updateHandler, UPDATE_SEARCH_SCHEMA):
                return
            handler = Matcherhandler(**updateHandler)
        else:
            if not self.validateJson(updateHandler, UPDATE_EXTRACT_SCHEMA):
                return
            handler = ExtractorHandler(**updateHandler)

        checkCompatibilityRes = checkCompatibilityHandlerPolicies(updateHandler)
        if checkCompatibilityRes.fail:
            return self.error(400, checkCompatibilityRes.errorCode, checkCompatibilityRes.description)

        esReply = yield es.putHandler(handler)
        if esReply.fail:
            return self.error(500, esReply.errorCode, esReply.description)
        HandlerManager.clearCache()
        self.success(200, handler.dict)

    @web.asynchronous
    @coRequestExeptionWrap
    @gen.coroutine
    def delete(self, handlerId):
        """
        Delete created handler.
        Response status codes:
            204 if handler was deleted
            500 if internal system error occurred

        :param handlerId:
        :return: None
        """
        esReply = yield es.deleteHandler(handlerId)
        if esReply.fail:
            return self.error(500, esReply.getErrorCode(), esReply.getErrorDescription())
        HandlerManager.clearCache()
        self.set_status(204)
        self.finish()
