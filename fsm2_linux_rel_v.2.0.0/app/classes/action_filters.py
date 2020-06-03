from app.common_objects import logger
from app.enums import FilterType, AttachRules
from common.switch import switch
from configs.config import GENDER_THRESHOLD
from errors.error import Error, Result


class ActionFilter:
    """
    Filter to decide to make or not an action. Filters are applied to a group or an event.

    There are the following filters: gender, age, similarity.

    Attributes:
        gender (int): 1 male, 0, female
        similarity_filter (dict): with policy and lists with thresholds for filtering
        age_range (dict): with two fields "start" and "end"
        type (int): object type, 1 for event, 2 for group

    """
    def __init__(self, isEventFilter = True, **kwargs):
        """
        :param isEventFilter:  type of objects for filtering, True - event, False - group
        :param kwargs: dict with params of filtering
        """

        self.similarity_filter = None
        self.gender = None
        self.age_range = None

        self.type = FilterType.EVENT if isEventFilter else FilterType.GROUP

        for member in self.__dict__:
            if member in kwargs:
                if member == "type":
                    continue
                self.__dict__[member] = kwargs[member]

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def isEventFilter(self):
        return self.type == FilterType.EVENT

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def generateIncompatibleError(filterName: str) -> Result:
        """
        Generate filter incompatibility error.

        :param filterName: name of filter where error is occurred
        :return: return Result(error, 500)
        """
        errorMsg = Error.IncompatibleError.getErrorDescription().format("create person, handler have {} "
                                                                        "filter, extract face does not have "
                                                                        "'attributes'".format(filterName))
        error = Error.generateError(Error.IncompatibleError, errorMsg)
        return Result(error, 500)

    def genderFilter(self, filteringObj) -> Result:
        """
        Filter by gender. Object pass this filter if gender is right.

        :param filteringObj: objectForFiltering: event or group
        :rtype: Result
        :return: 1) If object fits the conditions Result(Error.Success, True) will be returned;

                 #) If object does not fit the conditions Result(Error.Success, False) will be returned;

                 #) If filter cannot be applied to the object than Result with the incompatibility error will be
                 returned.
        :param filteringObj:

        """
        value = None
        if self.gender is not None:

            for case in switch(self.type):
                if case(FilterType.EVENT):
                    if "attributes" not in filteringObj.extract:
                        return ActionFilter.generateIncompatibleError("gender")
                    value = filteringObj.extract["attributes"]["gender"]
                    break
                if case(FilterType.GROUP):
                    if filteringObj.attributes.gender is None:
                        return ActionFilter.generateIncompatibleError("gender")
                    value = filteringObj.attributes.gender
                    break
                if case():
                    logger.error("Filter object not group or event")
                    error = Error.generateError(Error.UnknownError, 500)
                    return Result(error, 500)
            if self.gender != int(value > GENDER_THRESHOLD):
                return Result(Error.Success, False)
        return Result(Error.Success, True)

    def ageFilter(self, filteringObj) -> Result:
        """
        Filter by age. Object pass this filter if age belongs the age_range.

        :param filteringObj: objectForFiltering: event or group
        :rtype: Result
        :return: 1) If object fits the conditions Result(Error.Success, True) will be returned;

                 #) If object does not fits the conditions Result(Error.Success, False) will be returned;

                 #) If filters cannot be applied to the object than Result with error will be returned.
        """
        if self.age_range is not None:
            value = None
            for case in switch(self.type):
                if case(FilterType.EVENT):
                    if "attributes" not in filteringObj.extract:
                        return ActionFilter.generateIncompatibleError("age")
                    value = filteringObj.extract["attributes"]["age"]
                    break
                if case(FilterType.GROUP):
                    if filteringObj.attributes.age is None:
                        return ActionFilter.generateIncompatibleError("age")
                    value = filteringObj.attributes.age
                    break
                if case():
                    logger.error("Filter object not group or event")
                    error = Error.generateError(Error.UnknownError, 500)
                    return Result(error, 500)

            if self.age_range["start"] > value or self.age_range["end"] < value:
                return Result(Error.Success, False)
        return Result(Error.Success, True)

    def listsFilter(self, filteringObj) -> Result:
        """
        Filter by similarity.
        There are two results of this filter:
            1) Any of matches with lists has similarity greater than threshold.

            #) No one of matches with lists has similarity greater than threshold.

        :param filteringObj: objectForFiltering: event or group
        :rtype: Result
        :return: 1) If object fits the conditions Result(Error.Success, True) will be returned;

                 #) If object does not fits the conditions Result(Error.Success, False) will be returned;

                 #) If filters cannot be applied to the object than Result with error will be returned.
        """

        def matchHighFilter(filterOfList, searchRes, filterType):
            if searchRes["list_id"] == filterOfList["list_id"]:
                for case in switch(filterType):
                    if case(FilterType.EVENT):
                        if len(searchRes["candidates"]) == 0:
                            return Result(Error.Success, False)
                        if searchRes["candidates"][0]["similarity"] > filterOfList["threshold"]:
                            return Result(Error.Success, True)
                        break
                    if case(FilterType.GROUP):
                        if searchRes["candidate"]["similarity"] > filterOfList["threshold"]:
                            return Result(Error.Success, True)
                        break
                    if case():
                        logger.error("Filter object not group or event")
                        error = Error.generateError(Error.UnknownError, 500)
                        return Result(error, 500)
                else:
                    return Result(Error.Success, False)
            return Result(Error.Success, False)

        if self.similarity_filter is not None:
            highFilter = self.similarity_filter["policy"] == AttachRules.MATCH_HIGH_THAN

            for filterList in self.similarity_filter["lists"]:
                for searchResult in filteringObj.search:
                    filterRes = matchHighFilter(filterList, searchResult, self.type)
                    if filterRes.value:
                        return Result(Error.Success, highFilter)
            return Result(Error.Success, not highFilter)

        return Result(Error.Success, True)

    def filter(self, objectForFiltering) -> Result:
        """
        Apply filters to the object

        :param objectForFiltering: an event or a group
        :rtype: Result
        :return: 1) If object fits the conditions Result(Error.Success, True) will be returned;

                 #) If object does not fits the conditions Result(Error.Success, False) will be returned;

                 #) If filters cannot be applied to the object Result with error will be returned.
        """
        filterResult = self.genderFilter(objectForFiltering)
        if filterResult.fail or (not filterResult.value):
            return filterResult
        filterResult = self.ageFilter(objectForFiltering)

        if filterResult.fail or (not filterResult.value):
            return filterResult

        filterResult = self.listsFilter(objectForFiltering)
        if not filterResult.value:
            return filterResult
        return Result(Error.Success, True)
