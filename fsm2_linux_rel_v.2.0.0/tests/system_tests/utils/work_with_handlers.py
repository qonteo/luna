import copy


def generateHandlerWithDefault(handler):
    newHandler = copy.deepcopy(handler)
    groupingPolicyDefaults = {"age": 1, "gender": 2, "search": 2}
    if "grouping_policy" in newHandler:
        for default, value in groupingPolicyDefaults.items():
            if default not in newHandler["grouping_policy"]:
                newHandler["grouping_policy"][default] = value
    extractPolicyDefaults = {"estimate_quality": 0, "score_threshold": 0, "estimate_attributes": 0}
    if "extract_policy" not in newHandler:
        newHandler["extract_policy"] = extractPolicyDefaults
    for default, value in extractPolicyDefaults.items():
        if default not in newHandler["extract_policy"]:
            newHandler["extract_policy"][default] = value
    return newHandler


def compareLists(list1, list2):
    res = True
    if len(list1) != len(list2):
        return False
    for i in range(len(list1)):
        if type(list1[i]) != type(list2[i]):
            return False
        if type(list1[i]) is dict:
            return res and compareDict(list2[i], list1[i])
        if type(list1[i]) is list:
            return res and compareLists(list2[i], list1[i])
        return res and list2[i] == list1[i]
    return res


def compareDict(dict1, dict2):
    if dict1 is None or dict2 is None:
        return False

    if type(dict1) is not dict or type(dict2) is not dict:
        return False

    sharedKeys = set(dict2.keys()) & set(dict2.keys())

    if not (len(sharedKeys) == len(dict1.keys()) and len(sharedKeys) == len(dict2.keys())):
        return False

    dictsAreEqual = True
    for key in dict1.keys():
        if type(dict1[key]) is dict:
            dictsAreEqual = dictsAreEqual and compareDict(dict1[key], dict2[key])

        elif type(dict1[key]) is list:
            dictsAreEqual = dictsAreEqual and compareLists(dict1[key], dict2[key])
        else:
            dictsAreEqual = dictsAreEqual and (dict1[key] == dict2[key])

    return dictsAreEqual
