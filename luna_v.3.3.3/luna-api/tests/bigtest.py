import asyncio

from faker import Factory
from tornado import ioloop
import tornado
import datetime
import logbook
import os
import copy
import time
from tornado import gen
from logbook import Logger, StreamHandler
from functools import wraps
from tornado.options import OptionParser
import sys
from lunavl import httpclient
import ujson as json
import requests

from tornado.platform.asyncio import AnyThreadEventLoopPolicy

workPath = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

LIST_PERS_MUTABLE = "person list 1"  # reference for matching with
LIST_PERS_IMMUTABLE = "person list 2"  # list for detaching element from
LIST_DESC_MUTABLE = "descriptor list 1"  # reference for matching with
LIST_DESC_IMMUTABLE = "descriptor list 2"  # list for detaching element from


class oneListTemplate:
    def __init__(self, listId, listType, listData, count):
        self.listId = listId
        self.listType = listType
        self.listData = listData
        self.listCnt = count


class listsTemplate:
    def __init__(self):
        self.lists = []
        self.personListsCnt = 0
        self.descriptorsListCnt = 0

    def discount(self, isPerson):
        if isPerson is True:
            self.personListsCnt -= 1
        else:
            self.descriptorsListCnt -= 1

    def append(self, inpList):
        if inpList['listType'] is True:
            self.personListsCnt += 1
        else:
            self.descriptorsListCnt += 1
        self.lists.append(oneListTemplate(inpList['listId'], inpList['listType'], inpList['listData'], 0))

    def __delitem__(self, key):
        for lst in self.lists:
            if lst.listId == key:
                self.discount(lst.listType)
                self.lists.remove(lst)
                return
        for lst in self.lists:
            if lst.listData == key:
                self.discount(lst.listType)
                self.lists.remove(lst)
                return
        print('Error deleting list, required', key)

    def __getitem__(self, item):
        for lst in self.lists:
            if lst.listId == item:
                return lst
        for lst in self.lists:
            if lst.listData == item:
                return lst
        writeToLog("List not found, id or data: {}".format(item))
        sys.exit(3)

    @property
    def personsLists(self):
        return [lst for lst in self.lists if lst.listType]

    @property
    def descriptorsLists(self):
        return [lst for lst in self.lists if not lst.listType]


cmdOptions = None
fake = Factory.create()
StreamHandler(sys.stdout).push_application()

StreamHandler(sys.stdout).push_application()
logger = Logger('big_test')
logger.level = logbook.DEBUG

logger.handlers.append(logbook.FileHandler("./big_test_DEBUG.txt", level='DEBUG', bubble=True))
logger.handlers.append(logbook.FileHandler("./big_test_ERROR.txt", level='ERROR', bubble=True))

logFile = "big_test_" + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"


def timerTor(func):
    """
    Decorator for measuring the operation time of an asynchronous function.

    :param func: decorrated function.
    """
    @wraps(func)
    @gen.coroutine
    def wrap(*func_args, **func_kwargs):
        if __debug__:
            start = time.time()
            res = yield func(*func_args, **func_kwargs)
            end = time.time()
            logger.debug(func.__qualname__ + " time: " + str(round(end - start, 5)))
            return res
        else:
            res = yield func(*func_args, **func_kwargs)
            return res

    return wrap


def getOptionsParser():
    op = OptionParser()
    op.define('src', default='persons', help='folder with persons')
    op.define('luna_host', default="http://127.0.0.1", help='destination, ip address of luna python service')
    op.define('luna_port', default='5000', help='port of luna python service')
    op.define('luna_api', default=4, help='api version')
    op.define('c', help='level of concurrency', default=5, type=int)
    return op


def writeToLog(msg):
    with open(logFile, "a") as resFile:
        resFile.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + msg + "\n")
        resFile.close()
        logger.debug(msg)


def registration(payload):
    headers = {'Content-Type': 'application/json'}
    reply = requests.post(
        url='{}:{}/{}/accounts'.format(cmdOptions['luna_host'], cmdOptions['luna_port'], str(cmdOptions['luna_api'])),
                                       headers=headers, data=json.dumps(payload, ensure_ascii=False))
    return reply.json()


class BigTest:
    def __init__(self, concurrency=2, folderWithPerson=workPath + '/tests/persons'):
        self.concurrency = concurrency
        self.folderWithPersons = folderWithPerson

        self.descriptorCount, self.countAllPersons = 0, 0
        self.personsList, self.descriptorsList = [], []
        self.originPersonsDescriptors, self.listDescriptorsWIthPersons, self.folders, self.persons = [], [], [], []
        self.lists = listsTemplate()

        self.email = fake.email()
        self.orgName = fake.name()
        self.password = "secretpassword"

        payload = {"email": self.email,
                   "organization_name": self.orgName,
                   "password": self.password}
        self.token = registration(payload)['token']

        self.client = httpclient.LunaHttpClient(endPoint=cmdOptions['luna_host'], port=cmdOptions['luna_port'],
                                                api=cmdOptions['luna_api'], asyncRequest=True, login=self.email,
                                                password=self.password)

        writeToLog("login: " + self.email + ",")
        writeToLog("organization name: " + self.orgName + ",")
        writeToLog("password: " + self.password + ",")

    @timerTor
    @gen.coroutine
    def uploadOneFile(self, pathToFile):
        reply = yield self.client.extractDescriptors(filename=pathToFile, estimateAttributes=1, extractExif=1)
        return reply

    @timerTor
    @gen.coroutine
    def startUpload(self):
        for dirpath, dirnames, filenames in os.walk(self.folderWithPersons):
            self.folders.extend([(dirpath + "/" + g) for g in dirnames])
        self.countAllPersons = len(self.folders)

        self.uploadPersons()

        while len(self.persons) != len(self.folders):
            yield gen.sleep(0.1)

        return self.persons

    @timerTor
    @gen.coroutine
    def uploadPersons(self):
        iterByFolders = iter(self.folders)

        @gen.coroutine
        def worker():
            for folder in iterByFolders:
                yield self.uploadPerson(folder)
        yield [worker() for _ in range(self.concurrency)]

    @timerTor
    @gen.coroutine
    def uploadPerson(self, folderWithImage):
        files = []
        data = folderWithImage.split("/")[-1]
        for dirpath, dirnames, filenames in os.walk(folderWithImage):
            files = [dirpath + "/" + filename for filename in [g for g in filenames if g.endswith("jpg")]]

        reply = yield self.client.createPerson(data)

        if 200 > reply.statusCode > 299:
            writeToLog("Failed create person: {}".format(data))
            writeToLog(str(reply.body))
            sys.exit(10)

        person = {"id": reply.body["person_id"], "data": data, "descriptors": []}
        for file in files:

            reply = yield self.uploadOneFile(file)
            if 200 > reply.statusCode > 299:
                writeToLog("Failed upload descriptor: {}".format(file))
                writeToLog(str(reply.body))
                sys.exit(11)

            photoId = reply.body["faces"][0]["id"]
            person["descriptors"].append(photoId)
            reply = yield self.client.linkDescriptorToPerson(person['id'], photoId)
            if 200 > reply.statusCode > 299:
                writeToLog("Failed link person {} to descriptor: {}".format(person["id"], photoId))
                writeToLog(str(reply.body))
                sys.exit(12)

        writeToLog("Uploaded person {}".format(data))
        self.persons.append(person)

    def writeTableOfLists(self):
        rows = []
        rows.append('Descriptors lists, count {}'.format(self.lists.descriptorsListCnt))
        rows.append('{:=^77}'.format(""))
        rows.append('|{:<40}|{:<30}|{:<3}|'.format("List id", "List data", "Num"))
        rows.append('|{:-^40}|{:-^30}|{:-^3}|'.format("", "", ""))
        for descriptorsList in self.lists.descriptorsLists:
            tr = '|{:<40}|{:<30}|{:<3}|'.format(descriptorsList.listId, descriptorsList.listData,
                                                descriptorsList.listCnt)
            rows.append(tr)
        rows.append("")
        rows.append('Persons lists, count {}'.format(self.lists.personListsCnt))
        rows.append('{:=^77}'.format(""))
        rows.append('|{:<40}|{:<30}|{:<3}|'.format("List id", "List data", "Num"))
        rows.append('|{:-^40}|{:-^30}|{:-^3}|'.format("", "", ""))

        for personsList in self.lists.personsLists:
            tr = '|{:<40}|{:<30}|{:<3}|'.format(personsList.listId, personsList.listData,
                                                personsList.listCnt)
            rows.append(tr)
        rows.append("")
        for row in rows:
            writeToLog(row)

    def writeTableOfPersons(self):
        rows = []
        rows.append('Persons, count {}'.format(len(self.personsList)))
        rows.append('{:=^118}'.format(""))
        rows.append('|{:<40}|{:<30}|{:<3}|{:<40}|'.format("Person id", "User data", "Num",
                                                          "Descriptors"))
        rows.append('|{:-^40}|{:-^30}|{:-^3}|{:-^40}|'.format("", "", "", ""))
        for person in self.personsList:
            if len(person["descriptors"]) == 0:
                firstDescriptor = ""
            else:
                firstDescriptor = person["descriptors"][0]

            tr = '|{:<40}|{:<30}|{:<3}|{:<40}|'.format(person["id"], person["data"], len(person["descriptors"]),
                                                       firstDescriptor)
            rows.append(tr)
            if len(person["descriptors"]) > 1:
                for descriptor in person["descriptors"][1:]:
                    tr = '|{:<40}|{:<30}|{:<3}|{:<40}|'.format("", "", "", descriptor)
                    rows.append(tr)
        rows.append("")
        for row in rows:
            writeToLog(row)

    @gen.coroutine
    def createList(self, isPersonList, data):
        typeList = 'persons' if isPersonList else 'descriptors'
        reply = yield self.client.createList(typeList, data)
        if reply.statusCode != 201:
            writeToLog("FAILED CREATE LIST, type: {}, data: {}".format(typeList, data))
            sys.exit(2)
        self.lists.append({'listId': reply.body["list_id"], 'listType': isPersonList, 'listData': data})

    @timerTor
    @gen.coroutine
    def validateDescriptorsLists(self):
        for descriptorsList in self.lists.descriptorsLists:
            yield self.validateMatchingList(self.originPersonsDescriptors, descriptorsList.listId, False)

    @timerTor
    @gen.coroutine
    def uploadPerons(self):
        writeToLog("Start upload persons")
        self.personsList = yield self.startUpload()
        writeToLog("Persons uploaded, count: {}".format(len(self.personsList)))

    @timerTor
    @gen.coroutine
    def checkCountOfList(self, listId):
        reply = yield self.client.getList(listId)
        if not (200 <= reply.statusCode < 300):
            writeToLog("Failed get list info")
            writeToLog(str(reply.body))
            sys.exit(5)
        replyJson = reply.body
        listInfoCount = self.lists[listId].listCnt
        if listInfoCount != replyJson["count"]:
            writeToLog("Failed check count of object in list {}, {} vs {}".format(listId, listInfoCount,
                                                                                  replyJson["count"]))
            writeToLog(str(reply.body))
            sys.exit(6)
        writeToLog("success check list: {}".format(listId))

    @timerTor
    @gen.coroutine
    def attachLisObjectsToList(self, listId, listObjects, isPersons, action="attach"):
        writeToLog("Start attach objects to {}".format(listId))
        for i in range(int((len(listObjects) + 9) / 10)):
            forUpload = []
            for objectId in listObjects[10 * i: 10 * (i + 1)]:
                if isPersons:
                    reply = self.client.linkListToPerson(objectId, listId, action)
                else:
                    reply = self.client.linkListToDescriptor(objectId, listId, action)
                forUpload.append(reply)

            for request in forUpload:
                reply = yield request
                if not (200 <= reply.statusCode < 300):
                    writeToLog("Failed link object")
                    writeToLog(str(reply.body))
                    sys.exit(7)
                if action == "attach":
                    self.lists[listId].listCnt += 1
                else:
                    self.lists[listId].listCnt -= 1
        yield self.checkCountOfList(listId)
        writeToLog("Objects was attached to {}".format(listId))

    @gen.coroutine
    def attachPersonsToList(self, listId):
        writeToLog("Start attach persons to {}".format(listId))
        listPersonIds = [person["id"] for person in self.personsList]
        yield self.attachLisObjectsToList(listId, listPersonIds, True)
        writeToLog("Persons was attached to {}".format(listId))

    @timerTor
    @gen.coroutine
    def validateMatchingList(self, descriptors, listId, isPersonList):
        time.sleep(6)
        writeToLog("start validate list: {}".format(listId))
        for i in range(int((len(descriptors) + 9) / 10)):
            forUpload = []
            for descriptor in descriptors[10 * i: 10 * (i + 1)]:
                if isPersonList:
                    reply = self.client.identify(descriptorId=descriptor, listId=listId)
                else:
                    reply = self.client.match(descriptorId=descriptor, listId=listId)
                forUpload.append((reply, descriptor))
            for request in forUpload:
                reply = yield request[0]
                if not (200 <= reply.statusCode < 300):
                    writeToLog("failed match descriptor {} vs list {}".format(request[1], listId))
                    writeToLog(str(reply.body))
                    sys.exit(8)
                candidates = reply.body["candidates"]
                i = 0
                for candidate in candidates:
                    if isPersonList:
                        if candidate["descriptor_id"] == request[1]:
                            break
                    else:
                        if candidate["id"] == request[1]:
                            break
                    i += 1
                if i == len(candidates):
                    writeToLog("Failed matching validate {}, listId {}".format(request[1], listId))
                    writeToLog(str(reply.body))
                    sys.exit(9)
        writeToLog("success validate list: {}".format(listId))

    @timerTor
    @gen.coroutine
    def validatePerson(self, personId):
        listDescriptors = self.getPersonDescriptors(personId)
        for descriptor in listDescriptors:
            reply = yield self.client.verify(descriptor, personId)
            if not (200 <= reply.statusCode < 300):
                writeToLog("failed validate person {} vs descriptor {}".format(personId, descriptor))
                writeToLog(str(reply.body))
                sys.exit(13)
            candidate = reply.body["candidates"][0]
            if candidate["person_id"] != personId:
                writeToLog("failed validate person_id {} vs descriptor {}".format(personId, descriptor))
                writeToLog(str(reply.body))
                sys.exit(14)
            if candidate["descriptor_id"] != descriptor:
                writeToLog("failed validate descriptor_id {} vs descriptor {}".format(personId, descriptor))
                writeToLog(str(reply.body))
                sys.exit(15)

    @timerTor
    @gen.coroutine
    def validateRemoveDescriptorFromPerson(self, personId, descriptor):
        reply = yield self.client.verify(descriptor, personId)
        if not (200 <= reply.statusCode < 300):
            writeToLog("failed validate person {} vs descriptor {}".format(personId, descriptor))
            writeToLog(str(reply.body))
            sys.exit(16)
        cndidates = reply.body["candidates"]
        if len(cndidates) == 0:
            return
        candidate = cndidates[0]
        if candidate["person_id"] != personId:
            writeToLog("failed validate person_id {} vs descriptor {}".format(personId, descriptor))
            writeToLog(str(reply.body))
            sys.exit(17)
        if candidate["descriptor_id"] == descriptor:
            writeToLog("failed validate remove person {} vs descriptor_id {}".format(personId, descriptor))
            writeToLog(str(reply.body))
            sys.exit(18)

    @timerTor
    @gen.coroutine
    def validateListAfterRemoveDescriptor(self, listId, descriptor, byPersonsList):
        time.sleep(6)
        writeToLog("start validate removing descriptor from list: {}".format(listId))
        if byPersonsList is True:
            reply = yield self.client.identify(descriptorId=descriptor, listId=listId)
        else:
            reply = yield self.client.match(descriptorId=descriptor, listId=listId)
        if not (200 <= reply.statusCode < 300):
            writeToLog("failed validate removing descriptor {}, list {}".format(descriptor, listId))
            writeToLog(str(reply.body))
            sys.exit(19)

        candidates = reply.body["candidates"]

        if len(candidates) == 0:
            return
        for candidate in candidates:

            if candidate["descriptor_id"] == descriptor:
                writeToLog("failed validate removing descriptor {}, list {}, descriptor in list".format(descriptor,
                                                                                                             listId))
                writeToLog(str(reply.body))
                sys.exit(20)
        writeToLog("end validate removing descriptor from list: {}".format(listId))

    def getPersonsDescriptors(self):
        descriptors = []
        for person in self.personsList:
            descriptors.extend(person["descriptors"])
        return descriptors

    def getPersonDescriptors(self, persId):
        for person in self.personsList:
            if person["id"] == persId:
                return person["descriptors"]
        writeToLog("Failed find person: {}".format(persId))
        sys.exit(21)

    @timerTor
    @gen.coroutine
    def uploadImageAndAttachToPerson(self, person):
        writeToLog("start add new descriptors to person")
        files = []
        for dirpath, dirnames, filenames in os.walk(self.folderWithPersons + "/" + person["data"]):
            files = [dirpath + "/" + filename for filename in [g for g in filenames if g.endswith("jpg")]]

        for file in files:
            reply = yield self.uploadOneFile(file)
            if reply.statusCode > 299 or reply.statusCode < 200:
                writeToLog("Failed upload descriptor: {}".format(file))
                writeToLog(str(reply.body))
                sys.exit(22)

            photoId = reply.body["faces"][0]["id"]
            person["descriptors"].append(photoId)
            reply = yield self.client.linkDescriptorToPerson(person['id'], photoId)
            if reply.statusCode > 299 or reply.statusCode < 200:
                writeToLog("Failed link person {} to descriptor: {}".format(person["id"], photoId))
                writeToLog(str(reply.body))
                sys.exit(23)
        yield gen.sleep(0.5)
        writeToLog("add new descriptors {}".format(person["data"]))

    @timerTor
    @gen.coroutine
    def testDetachDescriptors(self):
        writeToLog("{:-^100}".format("Start test detach descriptors from person"))

        personForDetach = copy.deepcopy(self.personsList[0])
        for descriptor in personForDetach["descriptors"]:
            reply = yield self.client.linkDescriptorToPerson(personForDetach['id'], descriptor, 'detach')
            yield gen.sleep(0.5)
            if not (200 <= reply.statusCode < 300):
                writeToLog("failed detach descriptor {}, personId {}".format(descriptor, personForDetach["id"]))
                writeToLog(str(reply.body))
                sys.exit(24)
            self.personsList[0]["descriptors"].remove(descriptor)
            writeToLog("validate person after detach {}".format(personForDetach["data"]))
            yield self.validatePerson(personForDetach["id"])
            writeToLog("validate detach descriptor {} from person {}".format(descriptor, personForDetach["data"]))
            yield self.validateRemoveDescriptorFromPerson(personForDetach["id"], descriptor)

            currentPersDescriptors = self.getPersonsDescriptors()

            for accountList in self.lists.personsLists:
                yield self.validateMatchingList(currentPersDescriptors, accountList.listId, True)
                yield self.validateListAfterRemoveDescriptor(accountList.listId, descriptor, True)

            yield self.validateDescriptorsLists()

        yield self.uploadImageAndAttachToPerson(self.personsList[0])
        currentPersDescriptors = self.getPersonsDescriptors()
        yield gen.sleep(0.5)
        for accountList in self.lists.personsLists:
            yield self.validateMatchingList(currentPersDescriptors, accountList.listId, True)
        yield self.validateDescriptorsLists()

        writeToLog("{:-^100}".format("Test detach descriptors from person succeeded"))

    @timerTor
    @gen.coroutine
    def testDetachPersonFromList(self):
        writeToLog("{:-^100}".format("Start test detach person from list"))

        personForDetach = copy.deepcopy(self.personsList[0])

        writeToLog("Detach person")

        yield self.attachLisObjectsToList(self.lists[LIST_PERS_IMMUTABLE].listId, [personForDetach["id"]], True,
                                          "detach")
        yield gen.sleep(0.5)
        currentPersDescriptors = self.getPersonsDescriptors()
        yield self.validateMatchingList(currentPersDescriptors, self.lists[LIST_PERS_MUTABLE].listId, True)
        for descriptor in personForDetach["descriptors"]:
            yield self.validateListAfterRemoveDescriptor(self.lists[LIST_PERS_IMMUTABLE].listId, descriptor, True)

        yield self.validateDescriptorsLists()

        yield self.attachLisObjectsToList(self.lists[LIST_PERS_IMMUTABLE].listId, [personForDetach["id"]], True)
        yield gen.sleep(0.5)
        yield self.validateMatchingList(currentPersDescriptors, self.lists[LIST_PERS_IMMUTABLE].listId, True)

        yield self.validateDescriptorsLists()

        writeToLog("{:-^100}".format("Test detach person from list succeeded"))

    @timerTor
    @gen.coroutine
    def testDetachDescriptorsFromList(self):
        writeToLog("{:-^100}".format("Start test detach descriptor from list"))

        currentPersDescriptors = self.getPersonsDescriptors()
        detachDescriptor = list(set(currentPersDescriptors) & set(self.originPersonsDescriptors))[0]
        copyOrigin = copy.deepcopy(self.originPersonsDescriptors)
        copyOrigin.remove(detachDescriptor)

        listId = self.lists[LIST_DESC_IMMUTABLE].listId

        yield self.attachLisObjectsToList(listId, [detachDescriptor], False, "detach")
        yield gen.sleep(0.5)
        for accountList in self.lists.personsLists:
            yield self.validateMatchingList(currentPersDescriptors, accountList.listId, True)

        yield self.validateMatchingList(copyOrigin, listId, False)

        yield self.validateMatchingList(self.originPersonsDescriptors, self.lists[LIST_DESC_MUTABLE].listId, False)

        yield self.attachLisObjectsToList(listId, [detachDescriptor], False, "attach")
        yield gen.sleep(0.5)
        yield self.validateMatchingList(self.originPersonsDescriptors, listId, False)

        writeToLog("{:-^100}".format("Test detach descriptor from list succeeded"))

    @timerTor
    @gen.coroutine
    def testDeletePerson(self):
        writeToLog("{:-^100}".format("Start test delete person"))

        writeToLog("delete person")
        personForDelete = copy.deepcopy(self.personsList[0])
        reply = yield self.client.deletePerson(personForDelete["id"])
        if not (200 <= reply.statusCode < 300):
            writeToLog("failed delete person personId {}".format(personForDelete["id"]))
            writeToLog(str(reply.body))
            sys.exit(25)
        writeToLog("success delete person")

        self.personsList.remove(self.personsList[0])
        currentPersDescriptors = self.getPersonsDescriptors()
        for descriptor in personForDelete["descriptors"]:
            for accountList in self.lists.personsLists:
                yield self.validateMatchingList(currentPersDescriptors, accountList.listId, True)
                yield self.validateListAfterRemoveDescriptor(accountList.listId, descriptor, True)

        writeToLog("{:-^100}".format("Test delete person succeeded"))

    @timerTor
    @gen.coroutine
    def testDeletePersonsList(self):
        writeToLog("{:-^100}".format("Start test delete list of persons"))
        listId = self.lists[LIST_PERS_IMMUTABLE].listId
        reply = yield self.client.deleteList(listId)
        del self.lists[LIST_PERS_IMMUTABLE]
        yield gen.sleep(0.5)
        if not (200 <= reply.statusCode < 300):
            writeToLog("failed delete persons list {}".format(listId))
            writeToLog(str(reply.body))
            sys.exit(26)

        currentPersonsDescriptor = self.getPersonsDescriptors()

        yield self.validateMatchingList(currentPersonsDescriptor, self.lists[LIST_PERS_MUTABLE].listId, True)

        yield self.validateDescriptorsLists()

        writeToLog("{:-^100}".format("Test delete list of persons succeeded"))

    @timerTor
    @gen.coroutine
    def testDeleteDescriptorsList(self):
        writeToLog("{:-^100}".format("Start test delete list of descriptors"))

        descrsListId = self.lists[LIST_DESC_IMMUTABLE].listId
        reply = yield self.client.deleteList(descrsListId)

        if not (200 <= reply.statusCode < 300):
            writeToLog("failed delete descriptor list {}".format(descrsListId))
            writeToLog(str(reply.body))
            sys.exit(27)

        del self.lists[descrsListId]
        yield gen.sleep(0.5)

        if not (200 <= reply.statusCode < 300):
            writeToLog("failed delete descriptors list {}".format(descrsListId))
            writeToLog(str(reply.body))
            sys.exit(28)

        currentPersonsDescriptor = self.getPersonsDescriptors()

        yield self.validateMatchingList(currentPersonsDescriptor, self.lists[LIST_PERS_MUTABLE].listId, True)

        yield self.validateMatchingList(self.originPersonsDescriptors, self.lists[LIST_DESC_MUTABLE].listId,
                                        False)

        writeToLog("{:-^100}".format("Test delete list of descriptors succeeded"))

    @gen.coroutine
    def createLists(self):
        yield self.createList(True, LIST_PERS_MUTABLE)
        yield self.createList(True, LIST_PERS_IMMUTABLE)
        yield self.createList(False, LIST_DESC_MUTABLE)
        yield self.createList(False, LIST_DESC_IMMUTABLE)

    @gen.coroutine
    def startTest(self):
        start = time.time()
        formatLogTemplate = "{:=^100}"
        writeToLog(formatLogTemplate.format("Start Test"))
        writeToLog(formatLogTemplate.format("Start create lists"))

        yield self.createLists()

        writeToLog(formatLogTemplate.format("Lists created"))
        writeToLog(formatLogTemplate.format("Start create persons"))

        yield self.uploadPerons()

        writeToLog(formatLogTemplate.format("Persons created"))
        writeToLog(formatLogTemplate.format("Start attach persons to list"))

        for accountList in self.lists.personsLists:
            yield self.attachPersonsToList(accountList.listId)

        writeToLog(formatLogTemplate.format("Persons attached"))
        writeToLog(formatLogTemplate.format("Start attach descriptors to list"))

        self.originPersonsDescriptors = self.getPersonsDescriptors()
        for descriptorsList in self.lists.descriptorsLists:
            yield self.attachLisObjectsToList(descriptorsList.listId, self.originPersonsDescriptors, False)

        writeToLog(formatLogTemplate.format("Descriptors attached"))
        yield gen.sleep(0.5)

        writeToLog(formatLogTemplate.format("Start validate lists"))

        for accountList in self.lists.personsLists:
            yield self.validateMatchingList(self.originPersonsDescriptors, accountList.listId, True)

        yield self.validateDescriptorsLists()

        writeToLog(formatLogTemplate.format("Lists validated"))
        writeToLog(formatLogTemplate.format("Start validate persons"))

        for person in self.personsList:
            writeToLog("validate person {}".format(person["data"]))

            yield self.validatePerson(person["id"])

        writeToLog(formatLogTemplate.format("Persons validated"))
        writeToLog(formatLogTemplate.format("All data uploaded"))

        self.writeTableOfPersons()
        self.writeTableOfLists()

        writeToLog(formatLogTemplate.format("Start test detach Persons and descriptors"))

        yield self.testDetachDescriptors()
        yield self.testDetachPersonFromList()
        yield self.testDetachDescriptorsFromList()

        writeToLog(formatLogTemplate.format("Test detach Persons and descriptors succeeded"))

        self.writeTableOfPersons()
        self.writeTableOfLists()

        writeToLog(formatLogTemplate.format("Start test delete persons and lists"))

        yield self.testDeletePerson()
        yield self.testDeletePersonsList()
        yield self.testDeleteDescriptorsList()

        writeToLog(formatLogTemplate.format("Test delete persons and lists succeeded"))

        self.writeTableOfPersons()
        self.writeTableOfLists()
        end = time.time()
        writeToLog("{:!^100}".format("Test succeeded"))
        writeToLog("Time of test {} s".format(end-start))
        sys.exit(0)


if __name__ == '__main__':
    cmdOptions = getOptionsParser()
    cmdOptions.parse_command_line()
    test = BigTest()
    asyncio.set_event_loop_policy(AnyThreadEventLoopPolicy())
    tornado.ioloop.IOLoop.current().run_sync(test.startTest)