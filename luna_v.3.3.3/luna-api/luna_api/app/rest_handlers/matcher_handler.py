import tornado
from luna3.common.exceptions import LunaApiException
from tornado import gen, web
from typing import Tuple, List

from app.rest_handlers import validators
from app.rest_handlers.storage_handlers import StorageHandler
from app.rest_handlers.validators import Params
from crutches_on_wheels.utils.timer import timer

from crutches_on_wheels.errors.errors import Error, ErrorInfo
from crutches_on_wheels.errors.exception import VLException
from typing import List


def sortBySimilarity(el):
    """
    Returns similarity from matching result.

    :param el: one matching result
    :return: -el['similarity']
    """
    return -el['similarity']


def sortMatchingResult(arr):
    """
    Sort array by similarity to respond to matching.

    :param arr: respond array to matching
    :return: sorted array.
    """
    return sorted(arr, key=sortBySimilarity)


def getSimilarity(matchingRes, descriptorId):
    """
    Get similarity for id descriptor from LUNA.

    :param matchingRes: matching result in LUNA
    :param descriptorId: descriptor id
    :return: 0, id descriptor with descriptorId was not found
    """
    for candidate in matchingRes:
        if candidate["id"] == descriptorId:
            return candidate["similarity"]
    return 0


class MatchValidatorClass(object):
    """Structure for parsing query parameters during matching.

    Note:
        For every parameter Param must be class instance

    Attributes:
        :ivar limit:           maximum number of objects in responce, limited by MAX_CANDIDATE_IN_RESPONSE,\
         default 3.
        :ivar descriptor_id:   id of template descriptor
        :ivar list_id:         account list id
        :ivar descriptor_ids:  dynamic set of descriptor ids
        :ivar person_ids:      dynamic set of person ids
        :ivar candidateLength: number of candodates (for statistics).

    """

    def __init__(self):
        self.limit = Params(3, int, validators.limitValidator)
        self.descriptor_id = Params(None, str, lambda x: validators.validatorUUID(x, "descriptor_id"),
                                    validators.descriptorValidator)
        self.person_id = Params(None, str, lambda x: validators.validatorUUID(x, "person_id"),
                                validators.personIdValidator)

        self.list_id = Params(None, str, lambda x: validators.validatorUUID(x, "list_id"),
                              validators.accountListValidator)
        self.descriptor_ids = Params(None, list, lambda x: validators.validatorListUUIDStr(x, "descriptor_ids"),
                                     validators.descriptorsListValidator)
        self.person_ids = Params(None, list, lambda x: validators.validatorListUUIDStr(x, "person_ids"),
                                 validators.personsListValidator)
        self.candidateLength = 0


class MatcherHandler(StorageHandler, MatchValidatorClass):
    """
    Basic handler for matching
    """

    def __init__(self, *func_args, **func_kwargs):
        super().__init__(*func_args, **func_kwargs)
        MatchValidatorClass.__init__(self)

    def generateEmptyMatchingResult(self):
        """
        Send empty matching result

        :return: success(201, {"candidates": []})
        """
        return self.success(201, outputJson={"candidates": []})

    @gen.coroutine
    def matchAndUnion(self, template, candidateLists, prevMatchingResult, searchByLists=False):
        """
        Function for matching template with candidates list and for joining with previous results

        :param template:  reference descriptor id
        :param candidateLists: candidate list, list uuids
        :param prevMatchingResult: previous matching results
        :return: in case of success refer to connectResultMatching
        """

        self.candidateLength = len(candidateLists)

        matchRes = yield self.lunaCoreContext.match(template, candidateLists, searchByLists)
        matches = matchRes["matches"]

        connectResultRes = yield self.connectResultMatching(prevMatchingResult, matches)
        return connectResultRes

    def setQueryParameters(self, listParams):
        """
        Install lists parameters, that satisfy the query.

        :param listParams: list of possible query parameters
        :return: in case of success system returns Result with 0.
        """
        for param in listParams:
            try:
                paramValue = self.get_query_argument(param, None)
            except Exception as e:
                error = Error.formatError(Error.BadQueryParams, param)
                raise VLException(error, 400)
            if paramValue is not None:
                try:
                    self.__dict__[param].setValue(paramValue)
                except ValueError:
                    error = Error.formatError(Error.BadQueryParams, param)
                    raise VLException(error, 400)

    @staticmethod
    def generateErrorForHead(exception: LunaApiException) -> ErrorInfo:
        """
        Generate error for method head (now body with error)

        Args:
            exception: luna3 exception

        Returns:
            if status code 404 - object not found error otherwise Error.UnknownErrorFromLunaFaces
        Raises:
            VLException(error, e.statusCode, False): if method head and request failed
        """
        if exception.statusCode == 404:
            if exception.request.url.find("lists"):
                error = Error.ListNotFound
            elif exception.request.url.find("faces"):
                error = Error.FaceNotFound
            else:
                error = Error.PersonNotFound
        else:
            error = Error.UnknownErrorFromLunaFaces
        return error

    @gen.coroutine
    def getCandidatesForMatching(self, params):
        """
        Get list of candidates for matching

        Args:
            params: set of query parameters to get candidate list
        Returns:
            in case of success list of descriptors or list ids from LUNA is returned
        """
        for param in params:
            if not self.__dict__[param].isDefault:
                try:
                    resCheck = yield self.__dict__[param].dbValidator(self.__dict__[param].value, self.accountId,
                                                                      self.luna3Client)
                    return resCheck
                except VLException as e:
                    exception = VLException(e.error, 400, isCriticalError=False)
                    raise exception
                except LunaApiException as e:
                    if e.request.method != "HEAD" and e.statusCode != 599:
                        raise
                    error = self.generateErrorForHead(e)
                    raise VLException(error, e.statusCode if e.statusCode != 404 else 400, False)

        error = Error.formatError(Error.RequiredQueryParameterNotFound, params)
        raise VLException(error, 400, isCriticalError=False)

    @gen.coroutine
    def getTemplateForMatching(self, params):
        """
        Receive list of template descriptors.

        Args:
            List of query parameters
        Returns:
            in case of success system returns Result with list of template descriptors
        Raises:
            VLException(error, e.statusCode, False): if method head and request failed
        """
        for param in params:
            if not self.__dict__[param].isDefault:
                try:
                    resCheck = yield self.__dict__[param].dbValidator(self.__dict__[param].value, self.accountId,
                                                                      self.luna3Client)
                    return resCheck
                except VLException as e:
                    exception = VLException(e.error, 400, isCriticalError=False)
                    raise exception
                except LunaApiException as e:
                    if e.request.method != "HEAD" and e.statusCode != 599:
                        raise
                    error = self.generateErrorForHead(e)
                    raise VLException(error, e.statusCode if e.statusCode != 404 else 400, False)

        error = Error.formatError(Error.RequiredQueryParameterNotFound, params)
        raise VLException(error, 400, isCriticalError=False)

    def getTypeTemplate(self):
        """
        Get template type
        :return:  If type = person return 1, else return 0
        """
        if self.person_id.isDefault:
            return 1
        else:
            return 0

    def getTypeCandidate(self):
        """
        Get candidate type (dynamic or static list).

        :return:  If type = dynamic return 1, else return 0
        """
        if self.list_id.isDefault:
            return 1
        else:
            return 0

    def getStatSimilarity(self):
        """
        Get maximum similarity from response.

        :return: 0, if list is empty, else number in range from 0 to 1
        """
        candidates = self.statistiData.responseJson["candidates"]
        if len(self.statistiData.responseJson["candidates"]) > 0:
            candidate = candidates[0]
            return candidate["similarity"]
        else:
            return 0

    def setAdditionalDataToAdminStatistic(self, adminStats):
        """
        Set additional admin stats "limit", "template", "candidate", "value_sim", "value_time", "value_size"

        :param adminStats: common stats
        :return: new admin stats
        """
        newTags = {"limit": str(self.limit.value),
                   "template": str(self.getTypeTemplate()),
                   "candidate": str(self.getTypeCandidate())}
        newValues = {"value_sim": str(self.getStatSimilarity()),
                     "value_time": str(self.statistiData.requestTime),
                     "value_size": str(self.candidateLength)}
        adminStats.update(newTags, newValues)
        return adminStats

    def setAdditionalDataToAccountStatistic(self, accountStats):
        """
        Set template and candidate to stats

        :param accountStats: common request stats
        :return: new stats
        """

        if self.getResource() == "verify":
            accountStats["template"] = self.getRequestParam(["descriptor_id"])
            accountStats["candidate"] = self.getRequestParam(["person_id"])
        else:
            accountStats["template"] = self.getRequestParam(["person_id", "descriptor_id"])
            accountStats["candidate"] = self.getRequestParam(["person_ids", "descriptor_ids", "list_id"])
        return accountStats

    def getRequestParam(self, params):
        """
        Get query parameters of request

        note: It's assumed that at least one parameter exists

        :param params: list of possible parameters
        :return: dict is returned
        """
        for param in params:
            if not self.__dict__[param].isDefault:
                return {param: self.__dict__[param].value}
        self.logger.error("params not found, list params: " + str(params))

    @tornado.web.asynchronous
    @gen.coroutine
    def on_finish(self):
        """
        Function for sending request statistics

        note: Function is called after request was processed.
        """
        if self.request.method == "POST":
            yield self.sendStats()

    @gen.coroutine
    def connectResultMatching(self, currentResult, newMatchingResult):
        """
        Join new matching result with previous result. This operation is necessary as far as we do search,
        based on several reference person photos.

        :param currentResult: Current results
        :param newMatchingResult: New matching result
        :return: In case of success system returns joined result, list with dictionary with keys\
         person_id, similarity (best matching for all person descriptors), user_data,\
         descriptor_id of the best match.
        """
        if len(newMatchingResult) == 0:
            return currentResult
        photos = [candidate["id"] for candidate in newMatchingResult]

        personsReply = yield self.luna3Client.lunaFaces.getPersons(faceIds=photos, raiseError=True)
        candidates = list()
        for person in personsReply.json['persons']:
            for photo in photos:
                if photo in person['faces']:
                    candidates.append({'person_id': person['person_id'], 'face_id': photo})
        persons = {person["person_id"]: person for person in personsReply.json["persons"]}

        for candidate in candidates:
            i = 0
            while i < len(currentResult):
                if currentResult[i]["person_id"] == candidate["person_id"]:
                    if currentResult[i]["similarity"] < getSimilarity(newMatchingResult, candidate["face_id"]):
                        currentResult[i]["similarity"] = getSimilarity(newMatchingResult, candidate["face_id"])
                        currentResult[i]["descriptor_id"] = candidate["face_id"]
                    break
                i += 1
            if i == len(currentResult):
                currentResult.append({"similarity": getSimilarity(newMatchingResult, candidate["face_id"]),
                                      "person_id": candidate["person_id"], "descriptor_id": candidate["face_id"],
                                      "user_data": persons[candidate["person_id"]]["user_data"],
                                      "external_id": persons[candidate["person_id"]]["external_id"]})
        return currentResult

    @timer
    @gen.coroutine
    def getTemplatesAndCandidates(self, templatesParamNames=None, candidatesParamNames=None) -> Tuple[List, List]:
        if not templatesParamNames and not candidatesParamNames:
            return [], []
        candidates, templates = [], []
        try:
            if not templatesParamNames:
                candidates = yield self.getTemplateForMatching(candidatesParamNames)
            elif not candidatesParamNames:
                templates = self.getTemplateForMatching(templatesParamNames)
            else:
                candidates, templates = yield [self.getCandidatesForMatching(candidatesParamNames),
                                               self.getTemplateForMatching(templatesParamNames)]
        except LunaApiException as e:
            error = ErrorInfo(e.json["error_code"], e.json["desc"], e.json["detail"])
            if error == Error.ListNotFound or error == Error.PersonNotFound:
                raise VLException(error, 400, False)
            if error == Error.FaceNotFound:
                error = Error.DescriptorNotFound
                raise VLException(error, 400, False)
            raise
        return candidates, templates


class MatcherSearchHandler(MatcherHandler):
    """
    Handler of photo search request.

    .. http:post:: /matching/search?list_id=16fd2706-8baf-433b-82eb-8c7fada847d1&limit=1

        :optparam person_ids: dynamic list of candidate ids
        :optparam descriptor_ids: dynamic list of candidate ids
        :optparam list_id: account list id
        :optparam limit: maximum number of results in request
        :optparam estimate_emotions: Whether to estimate emotions from the image.

        :reqheader Authorization: basic authorization

                **or**

        :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

        :reqheader LUNA-Request-Id: request id

        For more information refer to :ref:`extract-label`, doesn't support flag "don't extract descriptor"

        :reqheader Content-Type:  "image/png", "image/x-portable-pixmap", "image/bmp", "image/tiff", "image/gif",
                         "image/x-windows-bmp"

        For data in base64 is sent:

        :reqheader Content-Type:  'image/x-jpeg-base64',
          'image/x-windows-bmp-base64', 'image/x-png-base64', 'image/x-portable-pixmap-base64',
          'image/x-bmp-base64", 'image/x-tiff-base64', 'image/x-gif-base64'

        .. sourcecode:: http

            POST /matching/search?list_id=16fd2706-8baf-433b-82eb-8c7fada847d1&limit=1 HTTP/1.1
            Accept: "image/png", "image/x-portable-pixmap", "image/bmp", "image/tiff", "image/gif",
                     "image/x-windows-bmp",
                    'image/x-windows-bmp-base64', 'image/x-png-base64', 'image/x-portable-pixmap-base64',
                    'image/x-bmp-base64", 'image/x-tiff-base64', 'image/x-gif-base64'

        **Example response**:

        :statuscode 201: matching is successful.

        .. sourcecode:: http

           HTTP/1.1 201 Created
           Vary: Accept
           Content-Type: application/json
           LUNA-Request-Id: 1516179740,c06887a2

        Search  by persons list

        .. json:object:: search_result_persons
            :showexample:

            :property candidates: matching result
            :proptype candidates: _list_(:json:object:`one_match_result_person`)
            :property face: extraction and matching were made for this face
            :proptype face: :json:object:`extract_one_descriptor`
            :property  exif: Select image EXIF tags. See CIPA DC-008-2016 for details. Tag to string conversions \
             are handled by libEXIF.
            :proptype exif: :json:object:`exif`

        Search by descriptors list.

        .. json:object:: search_result_descriptors
            :showexample:

            :property candidates: matching result
            :proptype candidates: _list_(:json:object:`one_match_result_descriptor`)
            :property face: extraction and matching were made for this face
            :proptype face: :json:object:`extract_one_descriptor`
            :property  exif: Select image EXIF tags. See CIPA DC-008-2016 for details. Tag to string conversions \
             are handled by libEXIF.
            :proptype exif: :json:object:`exif`

        Error message is returned in format :json:object:`server_error`.

        :statuscode 400: wrong type of query parameter
        :statuscode 400: too many faces in the picture
        :statuscode 500: internal server error

    """

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def post(self):
        self.setQueryParameters(["list_id", "person_ids", "descriptor_ids", "limit"])
        qParams = self.fillQueryParams()

        if qParams["extract_descriptor"] == 0:
            error = Error.formatError(Error.UnsupportedQueryParm, "extract_descriptor")
            return self.error(400, error)

        resLuna = yield self.lunaCoreContext.aggregateRequestParamAndSendPhotoToLuna(self.request.body,
                                                                                     self.request.headers,
                                                                                     qParams)

        faces = resLuna["faces"]
        for face in faces:
            photoId = face["id"]
            yield self.luna3Client.lunaFaces.putFace(photoId, attributesId=photoId, accountId=self.accountId,
                                                     raiseError=True)

        if len(faces) > 1:
            error = Error.generateError(Error.ManyFaces, resLuna)
            return self.error(400, error)
        face = faces[0]
        self.descriptor_id.setValue(face["id"])

        candidates, templates = yield self.getTemplatesAndCandidates(candidatesParamNames=["list_id", "person_ids",
                                                                                           "descriptor_ids"])

        def generateEmptyMatchingResult(extractingFace):
            response = {'candidates': [], "face": extractingFace}
            if qParams["extract_exif"]:
                response["exif"] = resLuna["exif"]
            return response

        if len(candidates) == 0:
            self.logger.debug("empty luna list for identify")
            return self.success(201, outputJson=generateEmptyMatchingResult(face))

        result = []
        searchByList = not self.list_id.isDefault
        listType = yield self.needPersonInAnswer()
        if listType:
            matchingRes = yield self.matchAndUnion(face["id"], candidates, result, searchByList)

            result = matchingRes
        else:
            matchingRes = yield self.lunaCoreContext.match(face["id"], candidates, searchByList)
            result = matchingRes["matches"]

        sortedResult = sortMatchingResult(result)

        if len(sortedResult) == 0:
            self.logger.debug("empty search result")
            return self.success(201, outputJson=generateEmptyMatchingResult(face))

        result = sortedResult[0: min(self.limit.value, len(result))]

        responseJs = {'candidates': result, "face": face}
        if qParams["extract_exif"]:
            responseJs["exif"] = resLuna["exif"]
        self.success(201, outputJson=responseJs)

    @gen.coroutine
    def needPersonInAnswer(self):
        if self.list_id.isDefault:
            return not self.person_ids.isDefault
        else:
            lunaListResponse = yield self.luna3Client.lunaFaces.getList(accountId=self.accountId, pageSize=0,
                                                                        listId=self.list_id.value, raiseError=True)
            return lunaListResponse.json["type"]


class MatcherVerifyHandler(MatcherHandler):
    """
    Handler for verification request. This request is necessary to match descriptor with person.
    """

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def post(self):
        """
        Handler for request to search for similar person

        .. http:post:: /matching/verify?descriptor_id=16fd2706-8baf-433b-82eb-8c7fada847d1&person_id=22fd2706\
            -8baf-433b-82eb-8c7fada847d1

            :optparam person_id:  Reference person id for matching
            :optparam descriptor_id:  descriptor id of candidate


            :reqheader Authorization: basic authorization

                    **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            :statuscode 201: Matching successful

            .. sourcecode:: http

               HTTP/1.1 201 Created
               Vary: Accept
               Content-Type: application/json

            .. json:object:: verify_result
               :showexample:

               :property candidates: matching result (array with one element)
               :proptype candidates: :json:object:`one_match_result_person`

            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: wrong type of query parameter
            :statuscode 500: internal server error

        """

        self.setQueryParameters(["descriptor_id", "person_id"])
        candidates, templates = yield self.getTemplatesAndCandidates(["descriptor_id"], ["person_id"])

        if len(candidates) == 0:
            self.logger.debug("empty luna list for identify")
            return self.generateEmptyMatchingResult()

        if len(templates) == 0:
            self.logger.debug("empty luna list for identify")
            return self.generateEmptyMatchingResult()

        result = []
        searchByList = not self.list_id.isDefault
        result = yield self.matchAndUnion(templates[0], candidates, result, searchByList)

        if len(result) == 0:
            self.logger.debug("empty verify result")
            return self.generateEmptyMatchingResult()

        sortedResult = sortMatchingResult(result)
        candidate = sortedResult[0]
        responseJs = {'candidates': [candidate]}
        self.success(201, outputJson=responseJs)


class MatcherIdentifyHandler(MatcherHandler):
    """
    Handler for identification request. This request is used to compare descriptors or persons
    """

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def post(self):
        """
        Handler for similar person search

        .. http:post:: /matching/identify?list_id=16fd2706-8baf-433b-82eb-8c7fada847d1&limit=1&person_id=22fd2706\
            -8baf-433b-82eb-8c7fada847d1

            :optparam person_ids: list of candidate person ids for matching
            :optparam list_id: account list id
            :optparam limit: maximum number of results in response
            :optparam person_id:  id of reference person
            :optparam descriptor_id:  id  of reference descriptor


            :reqheader Authorization: basic authorization

                    **or**

            :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

            :reqheader LUNA-Request-Id: request id

            **Example response**:

            :statuscode 201: Matching successful

            .. sourcecode:: http

               HTTP/1.1 201 Created
               Vary: Accept
               Content-Type: application/json

            .. json:object:: identify_result
               :showexample:

               :property candidates: matching result
               :proptype candidates: _list_(:json:object:`one_match_result_person`)

            Error message is returned in format :json:object:`server_error`.

            :statuscode 400: wrong type of query parameter
            :statuscode 500: internal server error

        """
        self.setQueryParameters(["list_id", "descriptor_id", "person_ids", "person_id", "limit"])

        candidates, templates = yield self.getTemplatesAndCandidates(["person_id", "descriptor_id"],
                                                                     ["list_id", "person_ids"])

        if len(candidates) == 0 or len(templates) == 0:
            self.logger.debug("empty luna list for identify")
            return self.generateEmptyMatchingResult()

        resultMatch = []
        searchByList = not self.list_id.isDefault
        for template in templates:
            resultMatch = yield self.matchAndUnion(template, candidates, resultMatch, searchByList)

        sortedResult = sortMatchingResult(resultMatch)
        if len(sortedResult) == 0:
            self.logger.debug("empty identify result")
            return self.generateEmptyMatchingResult()

        result = sortedResult[0: min(self.limit.value, len(resultMatch))]

        responseJs = {'candidates': result}
        self.success(201, outputJson=responseJs)


class MatcherDescriptorHandler(MatcherHandler):
    """
    Handler for similar descriptor search

    .. http:post:: /matching/match?list_id=16fd2706-8baf-433b-82eb-8c7fada847d1&limit=1&person_id=22fd2706\
        -8baf-433b-82eb-8c7fada847d1

        :optparam descriptor_ids: list of candidate person ids for matching
        :optparam list_id: id of descriptor list for account
        :optparam limit: maximum number of results in response
        :optparam person_id: id of reference person
        :optparam descriptor_id: id of reference decriptor

        :reqheader Authorization: basic authorization

                **or**

        :reqheader X-Auth-Token: '16fd2706-8baf-433b-82eb-8c7fada847da'

        :reqheader LUNA-Request-Id: request id

        **Example response**:

        :statuscode 201: Matching successful

        .. sourcecode:: http

           HTTP/1.1 201 Created
           Vary: Accept
           Content-Type: application/json

        .. json:object:: match_result
            :showexample:

            :property candidates: list with matching result
            :proptype candidates: _list_(:json:object:`one_match_result_descriptor`)

        Error message is returned in format :json:object:`server_error`.

        :statuscode 400: wrong type of query parameter
        :statuscode 500: internal server error

    """

    @StorageHandler.requestExceptionWrap
    @timer
    @gen.coroutine
    def post(self):
        self.setQueryParameters(["list_id", "descriptor_ids", "descriptor_id", "person_id", "limit"])

        candidates, templates = yield self.getTemplatesAndCandidates(["person_id", "descriptor_id"],
                                                                     ["list_id", "descriptor_ids"])
        if len(candidates) == 0 or len(templates) == 0:
            self.logger.debug("empty luna list for identify")
            return self.generateEmptyMatchingResult()

        resultMatch = []
        searchByList = not self.list_id.isDefault
        for photo in templates:
            matchRes = yield self.lunaCoreContext.match(photo, candidates, searchByList)

            resultMatch.extend(matchRes["matches"])

        def removeDuplicateDescriptorsFromResults(sortResult):
            descriptorIds = []
            res = []
            for matchResult in sortResult:
                descriptorId = matchResult["id"]
                if descriptorId not in descriptorIds:
                    res.append(matchResult)
                    descriptorIds.append(descriptorId)
            return res

        sortedResult = sortMatchingResult(resultMatch)
        sortedResult = removeDuplicateDescriptorsFromResults(sortedResult)
        if len(sortedResult) == 0:
            self.logger.debug("empty identify result")
            return self.generateEmptyMatchingResult()

        result = sortedResult[0: min(self.limit.value, len(resultMatch))]
        responseJs = {'candidates': result}
        self.success(201, outputJson=responseJs)
