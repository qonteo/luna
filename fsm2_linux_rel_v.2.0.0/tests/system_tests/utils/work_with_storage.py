from tests.system_tests.fsmRequests import emitEvent
from datetime import datetime


class EventStorage:
    def __init__(self, pathToImage, clusterId, handler):
        self.clusterId = clusterId
        self.descriptor = None
        self.person = None
        self.age = None
        self.gender = None
        self.img = pathToImage
        self.startUploadTime = None
        self.externalId = None
        self.handlerId = handler
        self.groupId = None
        self.id = None
        self.source = None
        self.tags = None

    def uploadImage(self, externalId, source, userData="", tags=None):
        self.externalId = externalId
        queryParams = {"external_id": self.externalId, "warped_img": 1, "source": source,
                       "user_data": userData}
        if tags is not None:
            queryParams["tags"] = ",".join(tags)
        event = emitEvent(self.handlerId, self.img, queryParams)
        self.startUploadTime = datetime.strptime(event.json["events"][0]["create_time"], '%Y-%m-%dT%H:%M:%SZ')
        self.age = event.json["events"][0]["extract"]["attributes"]["age"]
        self.gender = event.json["events"][0]["extract"]["attributes"]["gender"]
        self.descriptor = event.json["events"][0]["id"]
        self.person = event.json["events"][0]["person_id"]
        self.groupId = event.json["events"][0]["group_id"]
        self.source = source
        self.id = self.descriptor
        self.tags = tags if tags is not None else []

    def isSuitable(self, filters):
        for objectFilter in filters:
            if not objectFilter.comp(self.__dict__[filters.attribute]):
                return False
        return True


class GroupStorage:
    def __init__(self, events):
        self.age = sum([event.age for event in events]) / float(len(events))
        self.gender = sum([event.gender for event in events]) / float(len(events))
        self.tags = list(set().union(*[event.tags for event in events]))
        self.source = events[0].source
        self.groupId = events[0].groupId
        self.id = self.groupId
        self.handlerId = events[0].handlerId
        self.createTime = min([event.startUploadTime for event in events])
        self.clusterId = events[0].clusterId if events[0].clusterId != 2 else 1

    def isSuitable(self, filters):
        for objectFilter in filters:
            if not objectFilter.comp(self.__dict__[filters.attribute]):
                return False
        return True
