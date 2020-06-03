from typing import List, Optional, Union, Generator
from lunavl import luna_api
from lunavl.luna_response import LunaResponse
from tests.config import SERVER_ORIGIN, SERVER_API_VERSION
from tornado.httpclient import HTTPRequest
from tests.config import TEST_EMAIL, TEST_PASSWORD, TEST_ORGANIZATION_NAME
import json
import base64

SERVER_URL = "{}/{}".format(SERVER_ORIGIN, SERVER_API_VERSION)


def createAuthHeader(payload: Union[str, dict] = 'login', token: Optional[str] = '') -> dict:
    """
    The function creates authorization dictionary.

    Args:
        payload: 'login' or None for create authorization header with login, password or
                    'token' for create authorization header with token
        token: token - in uuid4 format

    Returns:
        dictionary in format {'token': "16fd2706-8baf-433b-82eb-8c7fada847da"} or
        {'login': 'hornsandhooves@ya.ru', 'password': 'secretpassword'}
    """
    if payload == 'login':
        return {'login': TEST_EMAIL, "email": TEST_EMAIL, 'password': TEST_PASSWORD,
                'organization_name': TEST_ORGANIZATION_NAME}
    elif payload == 'token':
        return {'token': token}
    else:
        if 'email' in payload: payload['login'] = payload['email']
        return payload


def createBadBase64BasicAuthHeader(login: Optional[str] = TEST_EMAIL, password: Optional[str] = TEST_PASSWORD) -> dict:
    """
    The function returns bad basic authorization dict from input login and password

    Args:
        login: login for authorization
        password: password for authorization

    Returns:
        dictionary if format {'Authorization': 'Basic hornsandhooves@ya.ru:c2VjcmV0cGFzc3dvcmQ='}
    """
    strAuth = password
    base64Auth = base64.b64encode(str.encode(strAuth)).decode("utf-8")
    badHeaders = {'Authorization': 'Basic ' + login + ":" + base64Auth}
    return badHeaders


def getAuthData(inputAuthData: Union[str, dict]) -> Union[dict, str]:
    """
    The function returns authorization header from inputAuthData or from default values

    Args:
        inputAuthData: dict with login and password or token for create header from inputs or nothing for create
                            header from default values

    Returns:
        dictionary in format {'token': "16fd2706-8baf-433b-82eb-8c7fada847da"} or
             {'login': 'hornsandhooves@ya.ru', 'password': 'secretpassword'}
    """
    if inputAuthData is not None:
        if 'Authorization' in inputAuthData and inputAuthData['Authorization'].startswith('Basic'):
            return inputAuthData
        authData = luna_api.createAuthHeader(inputAuthData)
    else:
        authData = luna_api.createAuthHeader(createAuthHeader())
    return authData


def manualRequest(resource: str, method: Optional[str] = "POST", body: Union[str, bytes] = None,
                  queryParams: Optional[dict] = None, headers: Optional[dict] = None, authData: Optional[dict] = None,
                  isBinary: Optional[bool] = False, asyncRequest: Optional[bool] = False
                  ) -> Union[Generator[None, None, LunaResponse], LunaResponse]:
    """
    The function create and execute request, if there isn't authorization headers in input values, it function create
    it from default values.

    Args:
        resource: resource for current request
        method: request method
        body: request bodyLunaResponse
        queryParams: query parametets
        headers: headers for request with or without authorization headeres
        authData: headers for authorization or empty if authorization headers in headers
        isBinary: binary flag
        asyncRequest: execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    if headers is None:
        headers = {}
    else:
        for element in headers:
            if element in ("token", "login", "password"):
                if authData is None: authData = {}
                authData[element] = headers[element]
    authData = getAuthData(authData)
    headers.update(authData)
    url = SERVER_URL + str(resource)
    if queryParams is not None:
        url += "?" + luna_api.generateStringQueryParams(queryParams)
    if not isBinary:
        body = json.dumps(body, ensure_ascii=False)
    request = HTTPRequest(url=url, method=method, body=body, headers=headers,
                          allow_nonstandard_methods=True)
    if asyncRequest:
        return luna_api.executeAsyncRequest(request, False)
    return luna_api.executeRequest(request, False)


def registration(payload: Optional[dict] = None) -> LunaResponse:
    """
    The function do simple registration with/without payload.

    Args:
        payload: dictionary with 'login' and 'password'

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    if payload is None: payload = createAuthHeader('login')  #: todo fix creating lists
    request = HTTPRequest(url=SERVER_URL + '/accounts', method='POST', body=json.dumps(payload),
                          headers={'Content-Type': 'application/json'}, allow_nonstandard_methods=True)
    return luna_api.executeRequest(request, False)


def getVersion(*args, **kwargs):
    """
    The wrapper function for getVersion from LUNA API.
    The function gets LUNA API version.

    Keyword Args:
        raiseError (bool): if request fails, LunaApiException is raised
        requestTimeOut (int): request's processing  timeout in seconds (20 by default)
        connectTimeOut (int): connection timeout in seconds.
        requestId (str): External request id. Helps uniquely identifying messages, corresponding to particular
                      requests, in system logs.
        requestId (str): External request id. Helps uniquely identifying messages, corresponding to particular
                      requests, in system logs.
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getVersion(SERVER_URL[:-2], *args, **kwargs)


def getAccountData(email: Optional[str] = None, password: Optional[str] = None, organization_name: Optional[str] = None,
                   token: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for getAccountData from LUNA API.
    The function gets account's data: email, organization name and status (whether the account is suspended or not).

    Args:
        email: account's login for authorization
        password: account's password for authorization
        organization_name: account's organization name for authorization
        token: account's token for authorization
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    if email is None and password is None and organization_name is None and token is None:
        authData = createAuthHeader('login')
    else:
        authData = {'login': email, 'password': password, 'organization_name': organization_name, 'token': token}
    return luna_api.getAccountData(lunaUrl=SERVER_URL, **authData, **kwargs)


def getTokens(authData: Optional[dict] = createAuthHeader(), tokenData: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for getTokens from LUNA API.
    The function gets account's tokens. Every token is represented ин *id* and *token data*.

    Args:
        authData: dict with login, password or token for authorization headers or empty if need to create it from
                     default values
        tokenData: part or whole token data to search by it
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getTokens(lunaUrl=SERVER_URL, tokenData=tokenData, **authData, **kwargs)


def createToken(login: Optional[str] = None, password: Optional[str] = None, tokenData: Optional[str] = '',
                **kwargs) -> LunaResponse:
    """
    The wrapper function for createToken from LUNA API.
    The function creates a token with token data. New token's *id* is returned.

    Args;
        login: account's login for authorization
        password: account's password for authorization
        tokenData: token data for token
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    if login is not None and password is not None:
        authData = {'login': login, 'password': password}
    else:
        authData = createAuthHeader('login')
    return luna_api.createToken(tokenData, lunaUrl=SERVER_URL, **authData, **kwargs)


def deleteTokens(authData: Optional[dict] = createAuthHeader(), tokens: Optional[List[str]] = '',
                 **kwargs) -> LunaResponse:
    """
    The wrapper function for deleteTokens from LUNA API.
    The function remove a tokens' list.

    Args:
        authData: dict with login, password or token for authorization headers or empty if need to create it from
                     default values
        tokens: list of token ids.
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.deleteTokens(tokens, lunaUrl=SERVER_URL, **authData, **kwargs)


def getToken(authData: Optional[dict] = createAuthHeader(), tokenId: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for getToken from LUNA API.
    The function gets *token data* of a token, which corresponds to *tokenId*.

    Args:
        authData: dict with login, password or token for authorization headers or empty if need to create it from
                     default values
        tokenId: token *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getToken(tokenId, lunaUrl=SERVER_URL, **authData, **kwargs)


def patchTokenData(authData: Optional[dict] = createAuthHeader(), tokenId: Optional[str] = None,
                   tokenData: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for patchTokenData from LUNA API.
    The function patches a token data for the token, which corresponds to *tokenId*.

    Args:
        authData: dict with login, password or token for authorization headers or empty if need to create it from
                     default values
        tokenId: token *id*
        tokenData: token data
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.patchTokenData(tokenId, tokenData, lunaUrl=SERVER_URL, **authData, **kwargs)


def deleteToken(authData: Optional[dict] = createAuthHeader(), tokenId: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for deleteToken from LUNA API.
    The function remove a token, which corresponds to *tokenId*.

    Args:
        authData: dict with login, password or token for authorization headers or empty if need to create it from
                     default values
        tokenId: token *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.deleteToken(tokenId, lunaUrl=SERVER_URL, **authData, **kwargs)


def getPersons(authData: dict, page: Optional[int] = 1, page_size: Optional[int] = 10, userData: Optional[str] = None,
               **kwargs) -> LunaResponse:
    """
    The wrapper function for getPersons from LUNA API.
    The function gets all persons of the account. Result is a list of persons and number of persons for the account.
    Each person is represented by *person_id*, *user_data*, *linked_descriptors*, linked_lists*.

    Args:
        authData: dict with login, password or token for authorization headers
        page: page number, positive.
        page_size: number of results per page, positive.
        userData: user data or part of user data to search by it
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getPersons(page=page, pageSize=page_size, userData=userData, lunaUrl=SERVER_URL, **authData,
                               **kwargs)


def createPerson(authData: dict, userData: Optional[str] = '', externalId: Optional[str] = None,
                 **kwargs) -> LunaResponse:
    """
    The wrapper function for createPerson from LUNA API.
    The function creates a person with user data. New person's *Id* is returned.

    Args:
        authData: dict with login, password or token for authorization headers
        userData: user data for person
        externalId: external id of the person, if it has its own mapping in external system
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.createPerson(userData=userData, externalId=externalId, lunaUrl=SERVER_URL, **authData, **kwargs)


def getPerson(authData: dict, personId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getPerson from LUNA API.
    The function gets a person, which corresponds to *personId*.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getPerson(personId=personId, lunaUrl=SERVER_URL, **authData, **kwargs)


def deletePerson(authData: dict, personId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for deletePerson from LUNA API.
    The function removes a person, which corresponds *personId*.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.deletePerson(personId=personId, lunaUrl=SERVER_URL, **authData, **kwargs)


def patchPerson(authData: dict, personId: str, userData: Optional[str] = None, externalId: Optional[str] = None,
                **kwargs) -> LunaResponse:
    """
    The wrapper function for patchPerson from LUNA API.
    The function patches *user_data* to the person.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person *id*
        userData: user data for person
        externalId: external id of the person, if it has its own mapping in external system
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.patchPerson(personId=personId, userData=userData, externalId=externalId, lunaUrl=SERVER_URL,
                                **authData, **kwargs)


def createList(authData: dict, listType: Optional[bool] = True, listData: Optional[str] = "", **kwargs) -> LunaResponse:
    """
    The wrapper function for createList from LUNA API.
    The function creates a list with list data. New list's *Id* is returned.

    Args:
        authData: dict with login, password or token for authorization headers
        listType: list's type ("persons" or "descriptors")
        listData: list data
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    listType = 'persons' if listType else 'descriptors'
    return luna_api.createList(listType=listType, listData=listData, lunaUrl=SERVER_URL, **authData,
                               **kwargs)


def getLists(authData: dict, userData: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for getLists from LUNA API.
    The function get all lists for the account.

    Args:
        authData: dict with login, password or token for authorization headers
        userData: part or whole list's user data to search by it
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getLists(lunaUrl=SERVER_URL, userData=userData, **authData, **kwargs)


def deleteLists(authData: dict, lists: Optional[List[str]] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for deleteLists from LUNA API.
    The function removes lists.

    Args:
        authData: dict with login, password or token for authorization headers
        lists: list of list ids.
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.deleteLists(lists, lunaUrl=SERVER_URL, **authData, **kwargs)


def getList(authData: dict, listId: str, page: Optional[int] = 1, pageSize: Optional[int] = 10,
            **kwargs) -> LunaResponse:
    """
    The wrapper function for getList from LUNA API.
    The function gets objects in the list.

    Args:
        authData: dict with login, password or token for authorization headers
        listId: list *id*
        page: page number, positive.
        pageSize: number of results per page, positive.
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getList(listId=listId, page=page, pageSize=pageSize, lunaUrl=SERVER_URL, **authData,
                            **kwargs)


def patchListData(authData: dict, listId: str, listData: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for patchListData from LUNA API.
    The function patches list data.

    Args:
        authData: dict with login, password or token for authorization headers
        listId: list *id*
        listData: list data
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.patchListData(listId, listData, lunaUrl=SERVER_URL, **authData, **kwargs)


def deleteList(authData: dict, listId: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for deleteList from LUNA API.
    The function removes a list.

    Args:
        authData: dict with login, password or token for authorization headers
        listId: list *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.deleteList(listId, lunaUrl=SERVER_URL, **authData)


def extractDescriptors(authData: dict, body: Optional[bytearray] = None, filename: Optional[str] = None,
                       userData: Optional[str] = None, warpedImage: bool = False,
                       extractDescriptor: bool = True, estimateQuality: bool = False,
                       contentType: Optional[str] = None, estimateAttributes: bool = False,
                       estimateEthnicities: bool = False, estimateEmotions: bool = False,
                       scoreThreshold: Optional[float] = 0, extractExif: bool = False,
                       pitchLt: Optional[float] = None, yawLt: Optional[float] = None, rollLt: Optional[float] = None,
                       estimateHeadPose: bool = False,
                       **kwargs) -> LunaResponse:
    """
    The wrapper function for extractDescriptors from LUNA API.
    Extract descriptors from a image. Image can be represented as raw bytes or path to file.

    Args:
        authData: dict with login, password or token for authorization headers
        body: image's bytes
        filename: path to the folder with the image
        userData: user data
        contentType: image mime type, if contentType is not set, will try to determine it by ourselves
                        raise ValueError if mimetype of content is not matches with acceptable formats
                        (Available mimetypes are: image/jpeg, image/png, image/gif, image/bmp, image/tiff,
                         application/x-vl-xpk, application/x-vl-face-descriptor, image/x-portable-pixmap)
        warpedImage: Determines, whether an input image is a warped or an arbitrary one. Exact image warping
                        algorithm is proprietary and this flag is intended for VisionLabs front-end tools only.

                        The warped image has the following properties:

                        * size is always 250x250 pixels;

                        * color format is always RGB;

                        * single face in a photo;

                        * the face is always centered and rotated so that imaginary line between the eyes is
                        horizontal.
        estimateAttributes: whether to estimate face attributes from the image or not(gender, age, glasses).
        estimateQuality: whether to estimate faces' suitability for recognition or not
        scoreThreshold: If estimate_quality parameter is set to 1, it is possible to apply a threshold check
                             to each estimation. All face detections with quality below the threshold are
                             ignored and no descriptors are extracted from them. The function proceeds as
                             usual with all the remaining detections (if left).
        extractDescriptor: whether to extract face descriptor(s) or nor.
        extractExif: Whether to extract EXIF meta information from the input image or not.

                        Exact output varies since there are no mandatory data writing requirements both to the authoring
                        software and digital cameras.

                        This function parses only the tags and outputs their names and values as-is.
        body: image's bytes
        filename: path to the folder with the image
        contentType: image mime type, if contentType is not set, will try to determine it by ourselves
                        raise ValueError if mimetype of content is not matches with acceptable formats
                        (Available mimetypes are: image/jpeg, image/png, image/gif, image/bmp, image/tiff,
                         application/x-vl-xpk, application/x-vl-face-descriptor, image/x-portable-pixmap)
        warpedImage: Determines, whether an input image is a warped or an arbitrary one. Exact image warping
                        algorithm is proprietary and this flag is intended for VisionLabs front-end tools only.

                        The warped image has the following properties:

                        * size is always 250x250 pixels;

                        * color format is always RGB;

                        * single face in a photo;

                        * the face is always centered and rotated so that imaginary line between the eyes is
                        horizontal.
        estimateAttributes: whether to estimate face attributes from the image or not(gender, age, glasses).
        estimateEmotions: whether to estimate emotions from the image.
        estimateEthnicities: whether to estimate ethnicities from the image.
        estimateQuality: whether to estimate faces' suitability for recognition or not
        scoreThreshold: If estimate_quality parameter is set to 1, it is possible to apply a threshold check
                             to each estimation. All face detections with quality below the threshold are
                             ignored and no descriptors are extracted from them. The function proceeds as
                             usual with all the remaining detections (if left).
        extractDescriptor: whether to extract face descriptor(s) or nor.
        yawLt: maximum deviation yaw angle from 0
        pitchLt: maximum deviation pitch angle from 0
        rollLt: maximum deviation roll angle from 0
        estimateHeadPose: whether to estimate head pose from the image
        extractExif: Whether to extract EXIF meta information from the input image or not.

                        Exact output varies since there are no mandatory data writing requirements both to the authoring
                        software and digital cameras.

                        This function parses only the tags and outputs their names and values as-is.
    Keyword Args:
        lunaUrl (str): base part of URL to Luna API with API version.
        raiseError (bool): if request fails, LunaApiException is raised
        requestTimeOut (int): request's processing  timeout in seconds (20 by default)
        connectTimeOut (int): connection timeout in seconds.
        login (str): account's login for authorization
        password (str): account's password for authorization
        asyncRequest (bool): execution in asynchronous mode, disabled by default
        requestId (str): External request id. Helps uniquely identifying messages, corresponding to particular
                      requests, in system logs.

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.extractDescriptors(body=body, filename=filename, lunaUrl=SERVER_URL, userData=userData,
                                       extractDescriptor=extractDescriptor, estimateQuality=estimateQuality,
                                       warpedImage=warpedImage, contentType=contentType,
                                       pitchLt=pitchLt, yawLt=yawLt, rollLt=rollLt,
                                       estimateAttributes=estimateAttributes, estimateEthnicities=estimateEthnicities,
                                       estimateEmotions=estimateEmotions, extractExif=extractExif,
                                       estimateHeadPose=estimateHeadPose,
                                       scoreThreshold=scoreThreshold, **authData, **kwargs)


def getDescriptors(authData: dict, page: Optional[int] = 1, pageSize: Optional[int] = 10,
                   userData: Optional[str] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for getDescriptors from LUNA API.
    The function gets accounts' descriptors. Result is a list of descriptors and number of descriptors
    for the account. Every descriptor is represented by *descriptor_id* and number of  *linked_lists*, the descriptor
    is attached to.

    Args:
        authData: dict with login, password or token for authorization headers
        page: page number, positive.
        pageSize: number of results per page, positive.
        userData: part or whole user data to search by it.
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getDescriptors(page=page, pageSize=pageSize, userData=userData, lunaUrl=SERVER_URL, **authData,
                                   **kwargs)


def getDescriptor(authData: dict, descriptorId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getDescriptor from LUNA API.
    The function gets the descriptor, which corresponds to *descriptorId*.

    Args:
        authData: dict with login, password or token for authorization headers
        descriptorId: descriptor *id*
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getDescriptor(descriptorId, SERVER_URL, **authData, **kwargs)


def linkDescriptorToPerson(authData: dict, personId: str, photoId: str, action: Optional[str] = 'attach',
                           **kwargs) -> LunaResponse:
    """
    The wrapper function for linkDescriptorToPerson from LUNA API.
    The function creates or deletes a link between a descriptor and a person.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id
        photoId: descriptor id
        action: "attach" or "detach"
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.linkDescriptorToPerson(personId, photoId, action, lunaUrl=SERVER_URL, **authData,
                                           **kwargs)


def getLinkedDescriptorToPerson(authData: dict, personId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getLinkedDescriptorToPerson from LUNA API.
    The function gets the list of descriptors, which are linked to a person.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getLinkedDescriptorToPerson(personId, lunaUrl=SERVER_URL, **authData, **kwargs)


def linkListToPerson(authData: dict, personId: str, listId: str, action: Optional[str] = 'attach',
                     **kwargs) -> LunaResponse:
    """
    The wrapper function for linkListToPerson from LUNA API.
    The function creates or deletes a link between a list and a person.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id
        listId: list id
        action: "attach" or "detach"
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.linkListToPerson(personId, listId, action, lunaUrl=SERVER_URL, **authData, **kwargs)


def link(authData: dict, listId: str, descriptorIds: Optional[List[str]] = None, personIds: Optional[List[str]] = None,
         action: str = 'attach', **kwargs) -> LunaResponse:
    """
    The wrapper function for link from LUNA API.
    The function creates or deletes a link between a list and persons or descriptors.

    Args:
        listId: list id
        authData: dict with login, password or token for authorization headers
        personIds: person ids
        descriptorIds: descriptor ids
        action: "attach" or "detach"

    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Return:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.link(listId, descriptorIds, personIds, action, lunaUrl=SERVER_URL, **authData, **kwargs)


def getLinkedListsToPerson(authData: dict, personId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getLinkedListsToPerson from LUNA API.
    The function gets the list of lists, which are linked to a person.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getLinkedListsToPerson(personId=personId, lunaUrl=SERVER_URL, **authData, **kwargs)


def linkListToDescriptor(authData: dict, photoId: str, listId: str, action: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for linkListToDescriptor from LUNA API.
    The function creates or deletes a link between a list and a descriptor.

    Args:
        authData: dict with login, password or token for authorization headers
        photoId: descriptor id
        listId:  list id
        action: "attach" or "detach"
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.linkListToDescriptor(photoId, listId, action, lunaUrl=SERVER_URL, **authData, **kwargs)


def getLinkedListsToDescriptor(authData: dict, descriptorId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getLinkedListsToDescriptor from LUNA API.
    The function gets the list of lists, the descriptor is linked to.

    Args:
        authData: dict with login, password or token for authorization headers
        descriptorId: descriptor id
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getLinkedListsToDescriptor(descriptorId=descriptorId, lunaUrl=SERVER_URL, **authData,
                                               **kwargs)


def getPortrait(authData: dict, photoId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for getPortrait from LUNA API.
    The function gets the portrait, which corresponds to *descriptorId*.

    Args:
        authData: dict with login, password or token for authorization headers
        photoId: descriptor id
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.getPortrait(descriptorId=photoId, lunaUrl=SERVER_URL, **authData, **kwargs)


def identify(authData: dict, personId: Optional[str] = None, descriptorId: Optional[str] = None,
             listId: Optional[str] = None, personIds: Optional[List[str]] = None, limit: Optional[int] = 3,
             **kwargs) -> LunaResponse:
    """
    The wrapper function for identify from LUNA API.
    The function matches a descriptor or person with a list of candidate persons.

    Either *descriptor_id* or *person_id* parameter should be specified as the reference and
    either *list_id* or *person_ids* parameter should be determined as the candidate.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id to take the reference descriptors from
        descriptorId: reference descriptor id.
        listId: candidate list id.
        personIds: list of candidate person ids
        limit: limit
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.identify(personId=personId, descriptorId=descriptorId, listId=listId, personIds=personIds,
                             limit=limit, lunaUrl=SERVER_URL, **authData, **kwargs)


def match(authData: dict, personId: Optional[str] = None, descriptorId: Optional[str] = None,
          listId: Optional[str] = None, descriptorIds: Optional[List[str]] = None, limit: Optional[int] = 3,
          **kwargs) -> LunaResponse:
    """
    The wrapper function for match from LUNA API.
    The function matches a descriptor or a person with a list of candidate descriptors.

    Either *descriptor_id* or *person_id* parameter should be specified as the reference and either *list_id* or
    *descriptor_ids*  parameter should be determined as the candidate.

    Args:
        authData: dict with login, password or token for authorization headers
        personId: person id to take the reference descriptors from
        descriptorId: reference descriptor id.
        listId: candidate list id.
        descriptorIds: list of candidate descriptor ids
        limit: limit
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        :return: structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.match(personId, descriptorId, listId, descriptorIds, limit, lunaUrl=SERVER_URL,
                          **authData, **kwargs)


def verify(authData: dict, descriptorId: str, personId: str, **kwargs) -> LunaResponse:
    """
    The wrapper function for verify from LUNA API.
    The function matches a descriptor with candidate person descriptors.

    Args:
        authData: dict with login, password or token for authorization headers
        descriptorId: reference descriptor id.
        personId: reference person id.
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.verify(descriptorId=descriptorId, personId=personId, lunaUrl=SERVER_URL,
                           **authData, **kwargs)


def search(authData: dict, body: Optional[bytearray] = None, filename: Optional[str] = None,
           contentType: Optional[str] = None, limit: Optional[int] = 3, warpedImage: Optional[bool] = False,
           estimateAttributes: Optional[bool] = False, estimateEmotions: Optional[bool] = False,
           estimateEthnicities: Optional[bool] = False, estimateQuality: Optional[bool] = False,
           estimateHeadPose: bool=False, pitchLt: Optional[float] = None, yawLt: Optional[float] = None,
           rollLt: Optional[float] = None,
           scoreThreshold: Optional[float] = 0, extractExif: Optional[bool] = False, listId: Optional[str] = None,
           descriptorIds: Optional[List[str]] = None, personIds: Optional[List[str]] = None, **kwargs) -> LunaResponse:
    """
    The wrapper function for search from LUNA API.
    The function extracts a descriptor from a photo, then matches it to a list of candidates.

    Either *list_id* or *person_ids* or *descriptor_ids* parameter should be specified as the candidate.

    Args:
        authData: dict with login, password or token for authorization headers
        body: image bytes
        filename: path to folder with the image
        contentType: image mime type, if contentType is not set, will try to determine it by ourselves
                        raise ValueError if mimetype of content is not matches with acceptable formats
                        (Available mimetypes are: image/jpeg, image/png, image/gif, image/bmp, image/tiff,
                        application/x-vl-xpk, application/x-vl-face-descriptor, image/x-portable-pixmap)
        warpedImage: Determines, whether an input image is a warped or an arbitrary one. Exact image warping
                        algorithm is proprietary and this flag is intended for VisionLabs front-end tools only.

                        The warped image has the following properties:

                        * size is always 250x250 pixels;

                        * color format is always RGB;

                        * single face in a photo;

                        * the face is always centered and rotated so that imaginary line between the eyes is
                           horizontal.
        estimateAttributes: whether to estimate face attributes for the image or not (gender, age, glasses).
        estimateQuality: estimate face suitability for recognition
        estimateEmotions: whether to estimate emotions from the image.
        estimateEthnicities: whether to estimate ethnicities from the image.
        yawLt: maximum deviation yaw angle from 0
        pitchLt: maximum deviation pitch angle from 0
        rollLt: maximum deviation roll angle from 0
        estimateHeadPose: whether to estimate head pose from the image
        scoreThreshold: If estimate_quality parameter is set to 1, it is possible to apply a threshold check
                             to each estimation. All face detections with the quality below the threshold are
                             ignored and no descriptors are extracted from them. The function proceeds as
                             usual with all the remaining detections (if left).
        extractExif: Whether to extract EXIF meta information from the input image or not.

                        Exact output varies since there are no mandatory data writing requirements both to the authoring
                        software and digital cameras.

                        This function only parses the tags and outputs their names and values as-is.
        listId: candidate list id.
        descriptorIds: list of candidate descriptor ids
        personIds: list of candidate person ids
        limit: limit
    Keyword Args:
        asyncRequest (bool): execution in asynchronous mode, disabled by default

    Returns:
        structure with status code, request and decoded Luna API response body is returned.
    """
    return luna_api.search(body=body, filename=filename, contentType=contentType, limit=limit, warpedImage=warpedImage,
                           estimateAttributes=estimateAttributes, estimateQuality=estimateQuality,
                           estimateEthnicities=estimateEthnicities, estimateEmotions=estimateEmotions,
                           scoreThreshold=scoreThreshold, estimateHeadPose=estimateHeadPose,
                           pitchLt=pitchLt, yawLt=yawLt, rollLt=rollLt,
                           extractExif=extractExif, listId=listId, descriptorIds=descriptorIds, personIds=personIds,
                           lunaUrl=SERVER_URL, **authData, **kwargs)
