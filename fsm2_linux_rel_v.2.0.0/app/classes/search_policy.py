from app.enums import SearchPriority


class SearchPolicy:
    """
    Handler policy. This policy regulates how input image will be searched.

    Attributes:
        search_lists (list):  Luna API list id list
        search_priority (SearchPriority): Max or by order
    """
    def __init__(self, **kwargs):
        self.search_lists = kwargs["search_lists"]
        self.search_priority = SearchPriority.MAX
        # self.limit = 1

        for member in self.__dict__:
            if member in kwargs:
                self.__dict__[member] = kwargs[member]

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
