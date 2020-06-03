from typing import Callable, Optional

from tornado import gen
from configs.config import MAX_CANDIDATE_IN_RESPONSE
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.handlers.query_getters import isUUID4


class Params:
    """
    Request structure.
    
    note:
        For every request parameter you have to specify expected parameter type, default value. You can optionally\
        specify parameter validator as value and validator value in database.
        
    Attributes:
        :ivar value: parameter value, when initializing parameter, value is set to default
        :ivar typeValue: parameter type
        :ivar formatValidator: parameter format validator, variable type is checked by default
        :ivar dbValidator: validator for checking parameter value accuracy in database. By default returns value
        :ivar isDefault: indicator that shows whether parameter was changed or not. 
    """

    def __init__(self, default, typeValue, validator: Optional[Callable] = None, dbValidator=None):
        self.value = default
        self.typeValue = typeValue
        self.isDefault = True
        if validator is None:
            def isValid(value):
                try:
                    value = self.typeValue(value)
                    return value
                except ValueError:
                    raise VLException(Error.BadQueryParams, 400, isCriticalError=False)

            self.formatValidator = isValid
        else:
            self.formatValidator = validator

        if dbValidator is None:
            def fakeValidator(value):
                return value

            self.dbValidator = fakeValidator
        else:
            self.dbValidator = dbValidator

    def setValue(self, value):
        """
        Function to set parameter value, *formatValidator* tests the parameter. In case of success, parameter value is
        set to value, returned by formatValidator
        and *isDefault* is set to False.
          
        :param value: raw parameter value.
        :return: in case of failure system returns value of *formatValidator*
        """
        self.value = self.formatValidator(value)
        self.isDefault = False


def validatorListUUIDStr(listUUIDStr, paramName):
    """
    Validator for UUID list, written in line and separated by comma.
    
    :param paramName: name of param
    :param listUUIDStr: list uuid4 in line, separated by comma
    :return: in case of success system returns Result with list uuid4.
    """
    uuids = listUUIDStr.split(',')
    for uuid in uuids:
        res = isUUID4(uuid)
        if not res:
            error = Error.formatError(Error.BadQueryParams, paramName)
            raise VLException(error, 400, isCriticalError=False)
    return uuids


def validatorUUID(uuid, paramName):
    res = isUUID4(uuid)
    if not res:
        error = Error.formatError(Error.BadQueryParams, paramName)
        raise VLException(error, 400, isCriticalError=False)
    return uuid


def limitValidator(limitStr):
    """
    Limit validator for matching, converted to int. If value is < 1, value is set to 3. If value is > \
    MAX_CANDIDATE_IN_RESPONSE, value is set to MAX_CANDIDATE_IN_RESPONSE.
    
    :param limitStr: str(int)
    :return: in case of success system returns Result with limit.
    """
    try:
        limitInt = int(limitStr)
    except ValueError:
        error = Error.formatError(Error.BadQueryParams, "limit")
        raise VLException(error, 400, isCriticalError=False)

    if limitInt < 1:
        limitInt = 3
    limit = min(MAX_CANDIDATE_IN_RESPONSE, limitInt)
    return limit


@gen.coroutine
def accountListValidator(listId, accountId, luna3Client):
    """
    Account list validator, checks whether account exists or not.

    :param luna3Client: luna3 client
    :param listId: list id
    :param accountId: account id
    :return: in case of success system returns Result with all list ids in Luna, which correspond to the account.
    """
    yield luna3Client.lunaFaces.checkList(accountId=accountId, listId=listId, raiseError=True)
    return [listId]


@gen.coroutine
def personIdValidator(personId, accountId, luna3Client, *args):
    """
    Person validator, checks whether person is linked to the account or not.
    
    :param luna3Client: luna3 client
    :param personId: person id
    :param accountId: account id
    :return: in case of success system returns Result with all person ids in Luna, which correspond to the accountId.
    """
    response = yield luna3Client.lunaFaces.personAttributes(personId=personId, accountId=accountId, raiseError=True)
    attributes = response.json["attributes_ids"]
    return attributes


@gen.coroutine
def descriptorValidator(photoId, accountId, luna3Client):
    """
    Descriptor validation. The existence of a descriptor for this account is checked.
    
    :param photoId: descriptor id
    :param accountId: account id
    :param luna3Client: luna3 client
    :return: in case of success system returns Result with list of [photoId]
    """
    response = yield luna3Client.lunaFaces.faceAttributes(faceId=photoId, accountId=accountId, raiseError=True)
    attributes = [response.json["attributes_id"]]
    return attributes


@gen.coroutine
def descriptorsListValidator(descriptorsList, accountId, luna3Client):
    """
    Descriptor list validation. The existence of all descriptors for this account is checked.
    
    :param descriptorsList: list of descriptor ids
    :param accountId: account id
    :param luna3Client: luna3 client
    :return: in case of success system returns Result with descriptorsList
    """
    descriptorsList = list(set(descriptorsList))
    descriptors = yield luna3Client.lunaFaces.facesAttributes(faceIds=descriptorsList, accountId=accountId,
                                                              raiseError=True)
    if len(descriptorsList) != len(descriptors.json):
        error = Error.formatError(Error.ObjectNotFound, "descriptors")
        raise VLException(error, 400, isCriticalError=False)
    attributes = [d['attributes_id'] for d in descriptors.json]
    return attributes


@gen.coroutine
def personsListValidator(personsList, accountId, luna3Client):
    """
    Person list validation. The existence of all persons for this account is checked.

    :param personsList: persons list id
    :param accountId:  account id
    :param luna3Client: luna3 client
    :return: in case of success system returns Result with all descriptor ids in Luna, which correspond to all persons.
    """
    personsList = list(set(personsList))
    persons = yield luna3Client.lunaFaces.personsAttributes(personIds=personsList, accountId=accountId,
                                                            raiseError=True)
    if len(personsList) != len(persons.json):
        error = Error.formatError(Error.ObjectNotFound, "person")
        raise VLException(error, 400, isCriticalError=False)

    attributes = [a for p in persons.json for a in p['attributes_ids']]
    return attributes
