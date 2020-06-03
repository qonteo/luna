from tornado import gen

from analytics.classes.list_linker import ListLinker
from analytics.classes.matcher import Matcher
from analytics.common_objects import timer, ES_CLIENT as es, LUNA_CLIENT, logger
from analytics.workers.tasks_functions import getFullLunaList, prepareFilters
from common.helpers import nestedGetter
from common.switch import switch
from common.tasks import Task
from errors.error import Result, Error


def updateDictWithAttributes(output_dict: dict, input_dict, path: list):
    """
    Update outputDict with 'age', 'gender' from input_dict in path.

    :param output_dict: output dict to update
    :param input_dict: input dict to update with
    :param path: attributes path in input dict
    :return: output_dict
    """
    for attr in ('age', 'gender'):
        output_dict[attr] = nestedGetter(input_dict, [*path, attr])
    return output_dict


class Clusterizer:
    """
    Class to divide objects into clusters.

    Attributes:
        task (Task): task to update the progress
        objectType (str): objects' type
        concurrency (float): count of synchronous functions to run
        objectsIds (list): object id list
        objects (list): full object list
        similarityMatrix (list): similarity matrix (index is the objectIds index)
        listForMatching (str): list id to match with
        deleteList (bool): if to delete list after clusterization or not
        threshold (float): the similarity threshold
        mapIdObject (dict): id->object_dict mapping
    """
    def __init__(self, task: Task, concurrency = 10, threshold = None):
        """
        :param task: task to update the progress
        :param concurrency: count of synchronous functions to run.
        """
        self.task = task
        self.objectType = None
        self.concurrency = concurrency
        self.objectsIds = []
        self.objects = []
        self.similarityMatrix = {}
        self.listForMatching = None
        self.deleteList = None
        self.threshold = threshold if threshold is not None else -1
        self.mapIdObject = {}

    @timer.timerTor
    @gen.coroutine
    def prepareDataFromList(self, weightOfPartOfTask):
        """
        Prepare data from Luna API list.

        :param weightOfPartOfTask: a progress delta to add after function completion
        :return: result
            Success if succeed
            Fail if an error occurred
        """
        self.listForMatching = self.task.task["filters"]["list_id"]
        gettingObjectsRes = yield getFullLunaList(self.listForMatching, self.concurrency)
        if gettingObjectsRes.fail:
            return gettingObjectsRes
        self.objectType = "persons" if "persons" in gettingObjectsRes.value else "descriptors"
        self.objects = gettingObjectsRes.value[self.objectType]
        self.objectsIds = [obj["id"] for obj in self.objects]
        self.mapIdObject = {obj["id"]: obj for obj in self.objects}
        self.task.progress += weightOfPartOfTask
        return Result(Error.Success, 0)

    @timer.timerTor
    @gen.coroutine
    def prepareDataFromEvents(self, weightOfPartOfTask):
        """
        Prepare data from events.

        :param weightOfPartOfTask: a progress delta to add after function completion
        :return: result
            Success if succeed
            Fail if an error occurred
        """
        self.objectType = "descriptors"
        filters = prepareFilters(self.task.task['filters'])
        referencesRes = yield es.getAll(es.SearchEvent(**filters),
                                        source = ['descriptor_id', 'source', "create_time",
                                                  'tags', 'extract.attributes.age', 'extract.attributes.gender'])
        if referencesRes.fail:
            self.task.addError(referencesRes)
            return referencesRes

        self.objects = []
        for event in referencesRes.value["hits"]:
            event_object = {"id": event["descriptor_id"],
                            "source": event["source"],
                            "create_time": event["create_time"],
                            "tags": event["tags"]}

            event_object = updateDictWithAttributes(event_object, event, ["extract", "attributes"])
            self.objects.append(event_object)

        self.objectsIds = [event['id'] for event in self.objects]
        self.mapIdObject = {event['id']: event for event in self.objects}

        createListReply = yield LUNA_CLIENT.createList("descriptors", "clusterization task {}".format(self.task.id))
        if not createListReply.success:
            self.task.addError(createListReply)
            return Result(Error.UnknownError, createListReply.body)

        self.listForMatching = createListReply.body["list_id"]
        linker = ListLinker(createListReply.body["list_id"], "descriptors", self.objectsIds, self.task,
                            weightOfPartOfTask)
        linkResult = yield linker.link()
        if linkResult.fail:
            return linkResult

        return Result(Error.Success, 0)

    @timer.timerTor
    @gen.coroutine
    def prepareDataFromGroups(self, weightOfPartOfTask):
        """
        Prepare data from groups.

        :param weightOfPartOfTask: a progress delta to add after function completion
        :return: result
            Success if succeed
            Fail if an error occurred
        """
        self.objectType = "descriptors"
        filters = prepareFilters(self.task.task['filters'])
        referencesRes = yield es.getAll(es.SearchGroup(**filters),
                                        ['id', 'descriptors', 'source', 'create_time', 'tags',
                                         'attributes.age', 'attributes.gender'])
        if referencesRes.fail:
            return referencesRes

        for group in referencesRes.value["hits"]:
            group_object = {"id": group["id"],
                            "source": group["source"],
                            "create_time": group["create_time"],
                            "tags": group["tags"],
                            "descriptors": group["descriptors"]}
            group_object = updateDictWithAttributes(group_object, group, ["attributes"])
            self.objects.append(group_object)

        for obj in referencesRes.value["hits"]:
            self.objectsIds.extend(obj['descriptors'])
            for descriptor in obj['descriptors']:
                descriptor_obj = {"id": obj["id"],
                                  "source": obj["source"],
                                  "create_time": obj["create_time"],
                                  "tags": obj["tags"],
                                  }
                descriptor_obj = updateDictWithAttributes(descriptor_obj, obj, ["attributes"])
                self.mapIdObject[descriptor] = descriptor_obj

        createListReply = yield LUNA_CLIENT.createList("descriptors",
                                                       "clusterization task {}".format(self.task.id))
        if not createListReply.success:
            self.task.addError(createListReply)
            return Result(Error.UnknownError, createListReply.body)

        self.listForMatching = createListReply.body["list_id"]
        linker = ListLinker(createListReply.body["list_id"], "descriptors", self.objectsIds, self.task,
                            weightOfPartOfTask)
        linkResult = yield linker.link()
        if linkResult.fail:
            return linkResult

        return Result(Error.Success, 0)

    @timer.timerTor
    @gen.coroutine
    def prepareData(self):
        """
        Choose prepare data function based on "objects" task parameter and run it.

        :return: result
            Success if succeed
            Fail if an error occurred
        """
        weightOfPartOfTask = 0.5
        for case in switch(self.task.task["objects"]):
            if case("luna_list"):
                self.deleteList = False
                res = yield self.prepareDataFromList(weightOfPartOfTask)
                return res
            if case("events"):
                self.deleteList = True
                res = yield self.prepareDataFromEvents(weightOfPartOfTask)
                return res
            if case("groups"):
                self.deleteList = True
                res = yield self.prepareDataFromGroups(weightOfPartOfTask)
                return res
            if case():
                error = Error.generateError(Error.ClusterErrorObjectType,
                                            Error.ClusterErrorObjectType.getErrorDescription().format(
                                                self.task.task["objects"]))
                return Result(error, self.task.task["objects"])

    @timer.timerTor
    @gen.coroutine
    def fillMatrixOfSimilarity(self):
        """
        Make matches and fulfill the similarity matrix.

        :return: result
            Success if succeed
            Fail if cross-match failed
        """
        matcher = Matcher(self.listForMatching, self.objectsIds, 5, self.task, 0.4, True, self.objectType)
        matchRes = yield matcher.match(self.concurrency)
        if matchRes.fail:
            return matchRes
        for reference, candidates in matchRes.value.items():
            if self.objectType == "descriptors":
                self.similarityMatrix.update(
                    {reference: [{"similarity": candidate["similarity"], "id": candidate["id"]} for
                                 candidate in candidates]})
            else:
                self.similarityMatrix.update(
                    {reference: [{"similarity": candidate["similarity"], "id": candidate["person_id"]} for
                                 candidate in candidates]})
        self.threshold = self.calculateThreshold()
        logger.debug("Task: {}, threshold: {}".format(self.task.id, self.threshold))
        return Result(Error.Success, 0)

    def calculateThreshold(self):
        """
        Threshold is generated as average similarity.

        :return: threshold
        """
        if self.threshold != -1:
            return self.threshold
        sumSimilarity = 0
        count = 0
        for candidates in self.similarityMatrix.values():
            for candidate in candidates:
                sumSimilarity += candidate["similarity"]
                count += 1
        return sumSimilarity / count

    def generateIncidenceMatrix(self):
        """
        Generate graph incidence matrix (id->[ids]) from similarity matrix according to the threshold.

        :return: ids matrix (row id is cluster number, row consists of associated clusters numbers)
        """
        matrix = [[] for i in range(len(self.objectsIds))]
        mapDescriptorNode = {objectId: i for i, objectId in enumerate(self.objectsIds)}

        for number, objectId in enumerate(self.objectsIds):
            for candidate in self.similarityMatrix[objectId]:
                if candidate["similarity"] >= self.threshold and candidate["id"] in mapDescriptorNode:
                    matrix[number].append(mapDescriptorNode[candidate["id"]])
        return matrix

    def getConnectedComponents(self, incidenceMatrix):
        """
        Merge components according to incidence matrix and groups if objects are groups.

        :param incidenceMatrix: filtered match matrix
        :return: merged components
        """
        def aggregateDescriptorsFromOneGroupToCluster():
            """
            Merge clusters.

            :return: None
            """
            mapDescriptorNode = {descriptor: i for i, descriptor in enumerate(self.objectsIds)}
            for group in self.objects:
                idx = [mapDescriptorNode[descriptor] for descriptor in group["descriptors"]]
                idx = sorted(idx)
                for i in idx[1:]:
                    mapNodeComponent[i] = idx[0]
                    self.mergeNodeComponents(idx[0], i, components, mapNodeComponent)

        components = [{i} for i in range(len(self.objectsIds))]
        mapNodeComponent = {i: i for i in range(len(self.objectsIds))}

        if self.task.task["objects"] == "groups":
            aggregateDescriptorsFromOneGroupToCluster()

        for i in range(len(self.objectsIds)):
            for j in incidenceMatrix[i]:

                cluster_i = mapNodeComponent[i]
                cluster_j = mapNodeComponent[j]
                if cluster_i == cluster_j:
                    continue

                self.mergeNodeComponents(cluster_i, cluster_j, components, mapNodeComponent)

        return [component for component in components if component is not None]

    @staticmethod
    def mergeNodeComponents(node1, node2, currentComponents, mapNodeComponent):
        """
        Merge nodes function. Node2 insert into Node1 and Node2 set None. Also update mappings.

        :param node1: node to merge in
        :param node2: node to merge from
        :param currentComponents: node->components list
        :param mapNodeComponent: component->node mapping
        :return: None
        """
        for component in currentComponents[node2]:
            mapNodeComponent[component] = node1
        currentComponents[node1] = currentComponents[node1] | currentComponents[node2]
        currentComponents[node2] = None

    def generateObjectClusters(self, clusters):
        """
        Replace Luna API objects (descriptors or persons) with FSM2 objects (descriptors, persons, events or groups)
        with its additional fields.

        :param clusters: objectId list list
        :return: list of clusters consisting of ful objects
        """
        objectClusters = []
        for cluster in clusters:
            newClusterObjId = set()
            newCluster = []
            for id in cluster:
                if self.mapIdObject[id]["id"] in newClusterObjId:
                    continue
                newClusterObjId.add(self.mapIdObject[id]["id"])
                newCluster.append(self.mapIdObject[id])
            objectClusters.append(list(newCluster))
        return objectClusters

    @timer.timer
    def generateClusters(self):
        """
        Generate clusters from connected components.

        :return: clusters
        """

        incidenceMatrix = self.generateIncidenceMatrix()
        components = self.getConnectedComponents(incidenceMatrix)

        clusters = []
        for component in components:
            clusters.append([self.objectsIds[index] for index in component])
        return clusters


