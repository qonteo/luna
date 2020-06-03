import copy


def sortMatchingResultByVoting(arr):
    """
    Sort voting results.

    :param arr: voting result list
    """
    sortedArr = sorted(arr, key = lambda x: -x["vote"])
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


def getVoters(searchResults):
    """
    Getting voters by search results.

    :param searchResults: search results, responses from luna api with candidates and similarity + filed "score of event
    :type searchResults: list
    :return: dict, keys - id of person or descriptor.
    """
    res = []

    for searchResult in searchResults:
        for candidate in searchResult["candidates"]:
            if "person_id" in candidate:
                res.append(candidate["person_id"])
            else:
                res.append(candidate["id"])

    res = list(set(res))
    return {voter: {"similarity": 0, "vote": 0, "count": 0} for voter in res}


def aggregateVotes(searchResults, voters):
    """
    Collecting votes for voters.

    :param searchResults: search results, responses from luna api with candidates and similarity + filed "score of event
    :type searchResults: list
    :param voters:
    :type voters: dict
    :return: update voters
    """
    for searchResult in searchResults:
        for count, candidate in enumerate(searchResult["candidates"]):
            if "person_id" in candidate:
                voter = voters[(candidate["person_id"])]
            else:
                voter = voters[(candidate["id"])]
            voter["vote"] += round((1 - count / len(searchResult["candidates"])) * searchResult["score"], 4)
            voter["count"] += 1
            voter["similarity"] += candidate["similarity"]

    for voter in voters:
        voters[voter]["vote"] = voters[voter]["vote"]
        voters[voter]["similarity"] = voters[voter]["similarity"] / voters[voter]["count"]
    return voters


def getCandidatesByVoting(searchResults, sortedVoters):
    """
    Collecting candidates by voting.

    :param searchResults: search results, list, items: dict with keys candidates, list_id, score
    :type searchResults: list
    :param sortedVoters: list with
    :return: list wth candidates
    """
    tempCandidatesStorage = {}

    for searchResult in searchResults:
        for count, candidate in enumerate(searchResult["candidates"]):
            if "person_id" in candidate:
                candidateId = candidate["person_id"]
            else:
                candidateId = candidate["id"]
            if candidateId not in tempCandidatesStorage:
                tempCandidatesStorage[candidateId] = copy.deepcopy(candidate)
                tempCandidatesStorage[candidateId]["listId"] = searchResult["list_id"]
            else:
                if candidate["similarity"] > tempCandidatesStorage[candidateId]["similarity"]:
                    tempCandidatesStorage[candidateId] = copy.deepcopy(candidate)
                    tempCandidatesStorage[candidateId]["listId"] = searchResult["list_id"]

    res = []
    for voter in sortedVoters:
        candidate = tempCandidatesStorage[voter["id"]]
        candidate["similarity"] = voter["similarity"]
        listId = candidate["listId"]
        del candidate["listId"]
        res.append({"candidate": candidate, "list_id": listId})

    return res


def majorityVoting(searchResults):
    """
    Majority voting.

    :param searchResults: search results, list, items: dict with keys candidates, list_id, score
    :type searchResults: list
    :rtype: list
    :return: list with candidates. Candidates is sorted by voter.
    """
    voters = getVoters(searchResults)
    voters = aggregateVotes(searchResults, voters)

    votersArray = [{"id": voter, "similarity": voters[voter]["similarity"],
                    "vote": voters[voter]["vote"]} for voter in voters]

    resVoters = sortMatchingResultByVoting(votersArray)
    return getCandidatesByVoting(searchResults, resVoters)
