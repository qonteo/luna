from tornado import gen
from app.common_objects import LUNA_CLIENT, logger
from app.classes.action_filters import ActionFilter
from app.classes.events import Event
from errors.error import Result, Error


class DescriptorPolicy:
    """
    Handler policy. This policy regulates attach descriptors to Luna API lists.

    Attributes:
        attach_policy (list): Luna API list id and filters list
    """
    def __init__(self, **kwargs):
        self.attach_policy = []

        for attachList in kwargs["attach_policy"]:
            attachListPolicy = {"list_id": attachList["list_id"]}
            if "filters" in attachList:
                attachListPolicy["filters"] = ActionFilter(**attachList["filters"])
            self.attach_policy.append(attachListPolicy)

    @gen.coroutine
    def executePolicy(self, event: Event) -> Result:
        """
        Execute policy for an event.

        :param event: event which corresponding of descriptor for attaching
        :rtype: Result
        :return: will return Result(Error.Success, True) if all operations be completed correctly
        """
        for attachList in self.attach_policy:
            listId = attachList["list_id"]
            if "filters" in attachList:
                needAttach = attachList["filters"].filter(event)
            else:
                needAttach = Result(Error.Success, True)
            if needAttach.fail:
                event.setError(needAttach.error)
                return needAttach
            if not needAttach.value:
                continue
            linkList = yield LUNA_CLIENT.linkListToDescriptor(event.descriptor_id, listId)
            if not linkList.success:
                error = Error.generateLunaError("Link list {} to descriptor".format(listId), linkList.body)
                logger.error(linkList.body)
                event.setError(error)
                return Result(error, linkList.statusCode)

            event.descriptors_lists.append(listId)

        return Result(Error.Success, True)

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
