from tornado import gen

from app.common_objects import LUNA_CLIENT, logger
from app.classes.action_filters import ActionFilter
from app.enums import FilterType
from common.switch import switch
from errors.error import Error, Result


def getDescriptorsFromObj(obj, typePolicy):
    """
    Returns descriptors from group or event.

    :param obj: group or event
    :param typePolicy: type of object
    :return: group.descriptors or [event.descriptor_id]
    """
    descriptorsForLinking = []
    for case in switch(typePolicy):
        if case(FilterType.EVENT):
            descriptorsForLinking = [obj.descriptor_id]
            break
        if case(FilterType.GROUP):
            descriptorsForLinking = obj.descriptors
            break
        if case():
            descriptorsForLinking = []
    return descriptorsForLinking


@gen.coroutine
def attachPersonFromObjCorrespondingPoliciesToList(personObject, attach_policy):
    """
    Attach the object person id to the list.

    :param personObject: object to get person id from
    :param attach_policy: attach policy
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    for attachList in attach_policy:
        listId = attachList["list_id"]
        if "filters" in attachList:
            needAttach = attachList["filters"].filter(personObject)
        else:
            needAttach = Result(Error.Success, True)
        if needAttach.fail:
            personObject.setError(needAttach.error)
            return needAttach
        if not needAttach.value:
            continue
        linkList = yield LUNA_CLIENT.linkListToPerson(personObject.person_id, listId)
        if not linkList.success:
            error = Error.generateLunaError("'Link list {} to person {}".format(listId, personObject.person_id),
                                            linkList.body)
            logger.error(linkList.body)
            personObject.setError(error)
            return Result(error, 0)
        personObject.persons_lists.append(listId)
    return Result(Error.Success, personObject)


@gen.coroutine
def createPerson(personObject, typePolicy):
    """
    Create person from object corresponding to the policy.

    :param personObject: object
    :param typePolicy: policy
    :return: result:
        Success if succeed
        Fail if an error occurred
    """
    if typePolicy == FilterType.EVENT:
        person = yield LUNA_CLIENT.createPerson(userData = personObject.user_data)
    else:
        person = yield LUNA_CLIENT.createPerson()
    if not person.success:
        lunaError = Error.generateLunaError("Create person ", person.body)
        logger.error(person.body)
        personObject.setError(lunaError)
        return Result(lunaError, person.statusCode)
    personObject.person_id = person.body["person_id"]
    descriptorsForLinking = getDescriptorsFromObj(personObject, typePolicy)

    futures = []
    for descriptor in descriptorsForLinking:
        futures.append(LUNA_CLIENT.linkDescriptorToPerson(personObject.person_id, descriptor))

    for linkDescriptorFuture in futures:
        linkResult = yield linkDescriptorFuture
        if not linkResult.success:
            lunaError = Error.generateLunaError("Link descriptor to person {}".format(personObject.person_id),
                                                linkResult.body)
            logger.error(linkResult.body)
            personObject.setError(lunaError)
    return Result(Error.Success, personObject)


class CreatePersonPolicy:
    """
       Handler policy. This policy person creation from object and person linking to list.

       Attributes:
           create_person(int): create or not person
           create_filters (ActionFilter): filters regulate person creation
           type (FilterType): type of object to make person from
           attach_policy (list): Luna API list id and filters list

    """
    def __init__(self, isEventPolicy, **kwargs):

        self.create_person = 1
        self.create_filters = ActionFilter(isEventPolicy)
        self.type = FilterType.EVENT if isEventPolicy else FilterType.GROUP
        if "create_filters" in kwargs:
            self.create_filters = ActionFilter(isEventPolicy, **kwargs["create_filters"])
        self.attach_policy = []

        if "attach_policy" in kwargs:
            for attachList in kwargs["attach_policy"]:
                attachListPolicy = {"list_id": attachList["list_id"]}
                if "filters" in attachList:
                    attachListPolicy["filters"] = ActionFilter(isEventPolicy, **attachList["filters"])
                self.attach_policy.append(attachListPolicy)

    @gen.coroutine
    def executePolicy(self, executionObject):
        """
        Execute policy for an object.

        Person will be created and attached to lists if object fits the filters.
        :param executionObject: input object
        :rtype: Result
        :return: result:
            Success if succeed
            Fail if an error occurred
        """
        if self.create_person == 0:
            return
        needCreate = self.create_filters.filter(executionObject)
        if needCreate.fail or (not needCreate.value):
            return needCreate

        createPersonRes = yield createPerson(executionObject, self.type)

        if createPersonRes.fail or (not createPersonRes.value):
            if createPersonRes.fail:
                executionObject.setError(createPersonRes.error)
                return createPersonRes
            return Result(Error.Success, 0)

        attachRes = yield attachPersonFromObjCorrespondingPoliciesToList(executionObject, self.attach_policy)
        return attachRes

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__


class PersonPolicy:
    """
    Handler policy. This policy regulates how a person will be created according to the object (event or group).
    """
    def __init__(self, isEventPolicy, **kwargs):
        self.create_person_policy = CreatePersonPolicy(isEventPolicy, **kwargs["create_person_policy"])

    @gen.coroutine
    def executePolicy(self, executionObject):
        res = yield self.create_person_policy.executePolicy(executionObject)
        return res

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
