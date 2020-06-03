from tornado import gen

from app.group_search_aggregators import aggregateDescriptorAggregator
from app.classes.person_policy import CreatePersonPolicy
from app.enums import Grouper, GenderChoice, AgeChoice, SearchChoice
from errors.error import Result, Error
from app.common_objects import logger


class GroupPolicy:
    """
    Handler policy. This policy regulates group processing.

    Attributes:
        grouper (int): Type of grouping events:
                        1 - group events by external id;
                        2 - group events by similarity (default);
                        3 - group events by external ids and similarity;
        ttl (int): group time to live, A group will close if no events were added to the group during this time period.
        threshold (float): threshold for grouping events by similarity.
        age (int): Type of age aggregation for group:
                        1 - mean
        gender (int): Type of gender aggregation for group:
                        1 - max deviation
                        2 - mean (default)
        search (int):  Type of search aggregation for group:
                        1 - top  by similarity
                        2 - majority voting (default)
                        3 - aggregate descriptor from all events and match it by all lists in search policy.

        create_person_policy: policy regulates creating person from group and attaching it to lists .
    """

    def __init__(self, **kwargs):
        self.grouper = Grouper.SIMILARITY.value
        self.ttl = 60
        self.threshold = 0.6
        self.gender = GenderChoice.MEAN.value
        self.age = AgeChoice.MEAN.value
        self.search = SearchChoice.MAJORITY_VOTING.value

        for member in self.__dict__:
            if member in kwargs:
                self.__dict__[member] = kwargs[member]
        self.create_person_policy = None
        if "create_person_policy" in kwargs:
            if kwargs["create_person_policy"] is not None:
                self.create_person_policy = CreatePersonPolicy(False, **kwargs["create_person_policy"])

    @gen.coroutine
    def executePolicy(self, group):
        """
        Execute create_person_policy for group.
        :param group: group of events
        :rtype: Result
        :return: in case of success Result(Error.Success, 0) will be returned
        """
        if self.search == SearchChoice.AGGREGATION.value:
            try:
                yield aggregateDescriptorAggregator(group)
            except Exception as e:
                logger.exception()
        if self.create_person_policy is not None:
            executeResult = yield self.create_person_policy.executePolicy(group)
            return executeResult
        return Result(Error.Success, 0)

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

