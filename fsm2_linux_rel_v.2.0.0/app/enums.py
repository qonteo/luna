from enum import Enum


class SearchPriority(Enum):
    MAX = 1
    BY_ORDER = 2

    def __repr__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other


class Grouper(Enum):
    EXTERNAL_ID = 1
    SIMILARITY = 2
    MIXED = 3

    def __repr__(self):
        return str(self.value)

    def __eq__(self, other):
        return self.value == other


class AttachRules(Enum):
    MATCH_LOW_THAN = 2
    MATCH_HIGH_THAN = 1

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class GenderChoice(Enum):
    MAX_DEVIATION = 1
    MEAN = 2

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class SearchChoice(Enum):
    TOP = 1
    MAJORITY_VOTING = 2
    AGGREGATION = 3

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class AgeChoice(Enum):
    MEAN = 1

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)


class FilterType(Enum):
    EVENT = 1
    GROUP = 2

    def __eq__(self, other):
        return self.value == other

    def __repr__(self):
        return str(self.value)

