"""
Module for aggregate search result for group
"""
import copy
import functools
from typing import List, Generator, Tuple

from app.common_objects import LUNA3_CLIENT, LUNA_CLIENT
from tornado import gen

from common.majority_voting import majorityVoting
from configs.config import LUNA_IMAGE_STORE_WARPS_BUCKET
from luna3.common.http_objs import Image
import uuid
from app.common_objects import ES_CLIENT as es


@gen.coroutine
def getWarps(warpIds: List[str]) -> Generator[None, None, List[bytes]]:
    """
    Get warps images from luna image store

    :param warpIds:warp ids
    :return: list with warps
    """
    responses = yield [LUNA3_CLIENT.lunaImageStore.getImage(LUNA_IMAGE_STORE_WARPS_BUCKET, id, raiseError=True) for id
                       in warpIds]
    return [response.body for response in responses]


@gen.coroutine
def aggregate(warpIds: List[str]) -> Generator[None, None, str]:
    """
    Aggregate descriptor and put it to api.

    :param warpIds: list ids of warps for aggregation
    :return: Aggregate descriptor id
    """
    warps = yield getWarps(warpIds)
    images = [Image(body=warp, filename=str(uuid.uuid4())) for warp in warps]
    response = yield LUNA3_CLIENT.lunaCore.extractDescriptor(images, aggregateDescriptor=True, warpedImage=True,
                                                             raiseError=True, asyncRequest=True)
    aggregateDescriptor = next(
        succeededImage["faces"][0]["id"] for succeededImage in response.json["succeeded_images"] if
        succeededImage["file_name"] == "aggregate")
    response = yield LUNA3_CLIENT.lunaCore.getDescriptor(aggregateDescriptor, raiseError=True, asyncRequest=True)
    response = yield LUNA_CLIENT.extractDescriptors(body=response.body, raiseError=True)
    return response.body["faces"][0]["id"]


@functools.lru_cache(maxsize=100)
@gen.coroutine
def getListsFromGroup(group) -> Generator[None, None, List[dict]]:
    """
    Get lists for matching from handler.

    :param group: group
    :return: list of dicts. Dicts contain list id and list type.
    """
    handlerRes = yield es.getHandler(group.handler_id)
    handler = handlerRes.value
    return handler["search_policy"]["search_lists"]


@gen.coroutine
def searchByList(searchList: dict, descriptorId: str) -> Generator[None, None, Tuple[List[dict], str]]:
    """
    Matching descriptor by list.

    :param searchList:  Dict contain list id and list type.
    :param descriptorId: descriptor id
    :return: match results and list id
    """
    listId = searchList["list_id"]
    listType = searchList["list_type"]
    limit = searchList["limit"]

    if listType == "persons":
        searchReply = yield LUNA_CLIENT.identify(descriptorId=descriptorId, listId=listId,
                                                 limit=limit, raiseError=True)
    else:
        searchReply = yield LUNA_CLIENT.match(descriptorId=descriptorId, listId=listId,
                                              limit=limit, raiseError=True)
    return searchReply.body["candidates"], listId


@gen.coroutine
def aggregateDescriptorAggregator(group) -> Generator[None, None, None]:
    """
    Create aggregate descriptor from all events of group and match it by lists from handler.

    :param group: group
    """
    aggregateDescriptorId = yield aggregate([event.id for event in group.events])
    lists = yield getListsFromGroup(group)
    responses = yield [searchByList(searchList, aggregateDescriptorId) for
                       searchList in lists]
    candidates = []
    for searchResult in responses:
        for candidate in searchResult[0]:
            candidates.append({"candidate": candidate, "list_id": searchResult[1]})
    group.search = sortMatchingResult(candidates)


def sortBySimilarity(el):
    """
    Returns similarity from a matching result.

    :param el: one matching result
    :return: -el['similarity']
    """
    return -el['candidate']['similarity']


def sortByVoting(el):
    """
    Returns vote from an element.

    :param el: one voting element
    :return: -el['vote']
    """
    return -el["vote"]


def sortMatchingResult(arr):
    """
    Sort array by similarity to respond the matching.

    :param arr: respond array to matching
    :return: sorted array.
    """
    return sorted(arr, key = sortBySimilarity)


def sortMatchingResultByVoting(arr):
    """
    Majority voting sort.

    :param arr: input array. Elements should have "vote" item.
    :return: sorted array
    """
    sortedArr = sorted(arr, key = sortByVoting)
    if len(sortedArr) == 0:
        return sortedArr
    currentVoting = sortedArr[0]["vote"]
    startIndex = 0
    endIndex = 1
    i = 0
    for el in sortedArr[1:]:
        i += 1
        if currentVoting == el["vote"]:
            endIndex = i + 1
            continue
        else:
            currentVoting = el["vote"]
            if endIndex - startIndex == 1:
                startIndex = i
                endIndex = i + 1
                continue
            partOfArr = sortedArr[startIndex: endIndex]
            sortedArr[startIndex: endIndex] = sorted(partOfArr, key = lambda x: -x["similarity"])
            startIndex = i
            endIndex = i + 1
    return sortedArr


def top3Aggregator(group):
    """
    Returns the most actual search results for event group.

    :param group: group
    :return: aggregated max search
    """
    candidates = []
    for event in group.events:
        if event.search is not None:
            for searchResult in event.search:
                for candidate in searchResult["candidates"]:
                    candidates.append({"candidate": candidate, "list_id": searchResult["list_id"]})
        else:
            return None
    sortedResult = sortMatchingResult(candidates)

    def isSameType(candidate1, candidate2):
        """
        Shows if search reply candidates are the same type.

        :param candidate1: first candidate
        :param candidate2: second candidate
        :return: True or False
        """
        return ("person_id" in candidate1) == ("person_id" in candidate2)

    def inRes(resArray, candidate):
        """
        Shows if the candidate is in a candidate list.

        :param resArray: a candidates list
        :param candidate: the candidate
        :return: True or False
        """
        lunaRes = candidate["candidate"]
        for element in resArray:
            if not isSameType(element["candidate"], lunaRes):
                continue
            if "person_id" in lunaRes:
                if element["candidate"]["person_id"] == lunaRes["person_id"]:
                    return True
            else:
                if element["candidate"]["id"] == lunaRes["id"]:
                    return True
        return False

    res = []
    for candidate in sortedResult:
        if not inRes(res, candidate):
            res.append(candidate)

        if len(res) == 3:
            break
    return res


def majorityVotingAggreagator(group):
    """
    Returns top-3 search results from group's events.

    :param group:
    :return:
        if search results exist: top 3 majority voted search results
        if search result does not exist: None
    """
    searchResults = []

    for event in group.events:
        if event.search is not None:
            for searchResult in event.search:
                copySearchResult = copy.deepcopy(searchResult)
                copySearchResult["score"] = event.extract["score"]
                searchResults.append(copySearchResult)
        else:
            return None

    return majorityVoting(searchResults)[:3]