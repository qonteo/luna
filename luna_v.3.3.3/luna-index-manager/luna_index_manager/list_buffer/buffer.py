"""
Module realize buffer for storage luna lists.
"""
from datetime import datetime
from collections import deque
from typing import List, Optional, Union


class LunaList:
    """
    Container for luna list from luna-faces.

    Attributes:
        listId: list id from luna core
        lastUpdateTime: list last update time (data from luna-faces)
        countFaces: face count (data from luna-faces)
    """

    def __init__(self, listId: str, lastUpdateTime: datetime, countFaces: int):
        self.listId = listId
        self.lastUpdate = lastUpdateTime
        self.faceCount = countFaces

    def __eq__(self, other):
        return self.listId == other.listId

    @property
    def asDict(self):
        res = {"list_id": self.listId, "face_count": self.faceCount,
               "last_update_time": self.lastUpdate}
        return res


class ListBuffer:
    """
    Buffer for waiting of index lists
    Attributes:
        listsForIndexing (deque): deque of luna list
        lastUpdate (datetime): buffer last update time
    """

    def __init__(self):

        self.listsForIndexing = deque()
        self.lastUpdate = datetime.now()

    def push(self, lunaList: LunaList) -> None:
        """
        Add luna list to buffer.

        If list with same id already in buffer will update data

        Args:
            lunaList: luna list
        """
        for number, waitingList in enumerate(self.listsForIndexing):
            if waitingList.listId == lunaList.listId:
                self.listsForIndexing[number] = lunaList
                return
        self.listsForIndexing.appendleft(lunaList)

    def forwardList(self, lunaList):
        try:
            self.listsForIndexing.remove(lunaList)
        except ValueError:
            pass
        self.listsForIndexing.append(lunaList)


    def extend(self, lists: List[LunaList]) -> None:
        """
        Add lists for indexing

        Args:
            lists: luna lists
        """
        self.lastUpdate = datetime.now()
        [self.push(lunaList) for lunaList in lists]
        map(self.push, lists)

    def pop(self) -> Optional[LunaList]:
        """
        Pop list for indexing.

        Returns:
            luna list if buffer is not empty otherwise None
        """
        if len(self.listsForIndexing) > 0:
            return self.listsForIndexing.pop()
        return None

    def clear(self) -> None:
        """
        Clear buffer
        """
        self.listsForIndexing.clear()

    def __getitem__(self, key: Union[slice, int]) -> Union[List[LunaList], LunaList, None]:
        """
        Get items from
        Args:
            key: the accepted keys should be integers and slice objects

        Returns:
            list of object if key is slice otherwise  luna list or None
        """
        if isinstance(key, slice):
            res = []
            for index, lunaList in enumerate(self.listsForIndexing):
                if key.start <= index < key.stop:
                    res.append(lunaList)
            return res

        return self.listsForIndexing[key]
