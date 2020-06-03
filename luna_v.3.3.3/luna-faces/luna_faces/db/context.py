from functools import wraps
from configs.config import DB
from datetime import datetime
from sqlalchemy import and_, insert, update, delete, func, select, exists, or_, union_all
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Tuple, Union, Any

from crutches_on_wheels.utils.log import Logger
from db import engine
import sys
from itertools import groupby
from luna3.common.timer import contextTime
from db.models import LINK_SEQUENCE

if sys.argv[0].find("sphinx") == -1:
    from db import models

from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.functions import convertTimeToString
from sqlalchemy.orm import Query, aliased
from configs.config import STORAGE_TIME
from uuid import uuid4


class NotUpdatedError(ValueError):
    """
    Exception for failed update queries.

    Raise this exception if your update did not work
    """


def currentTimestamp() -> Union[str, datetime]:
    """
    Function get time (local or UTC, depends on TIME_STORAGE in config)

    Returns:
        Timestamp if format '%Y-%m-%dT%H:%M:%S.%fZ'
    """
    timestamp = datetime.utcnow() if STORAGE_TIME == 'UTC' else datetime.now()
    if DB == 'oracle':
        return timestamp
    else:
        return timestamp.isoformat('T')


def exceptionWrap(wrapFunc):
    """
    Decorator for catching exceptions when composing queries to the database.

    Args:
        wrapFunc: function

    Returns:
        If exception is not caught, function result is returned, else Result\
        with value of exception is returned
    """

    @wraps(wrapFunc)
    def wrap(*func_args, **func_kwargs):
        try:
            return wrapFunc(*func_args, **func_kwargs)
        except (VLException, NotUpdatedError, TypeError):
            raise
        except Exception as e:
            func_args[0].logger.exception()
            raise VLException(Error.ExecuteError)

    return wrap


class DBContext:
    """
    DB context

    Attributes:
        logger: request logger
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    @exceptionWrap
    def createFace(self, externalFaceId: Optional[str] = None, **kwargs) -> str:
        """
        Create face

        Args:
            externalFaceId: external faceId

        Keyword Args:
                event_id: reference to event which created face
                attributes_id: attribute id
                user_data: face information
                account_id: id of account, required
                external_id: external id of the face, if it has its own mapping in external system

        Raises:
            IntegrityError

        Returns:
            faceId: face id in uuid4 format
        """
        faceId = str(uuid4()) if externalFaceId is None else externalFaceId
        try:
            with engine.begin() as connection:
                createTime = currentTimestamp()
                lastUpdate = currentTimestamp()
                insertSt = insert(models.Face).values(face_id=faceId,
                                                      create_time=createTime,
                                                      last_update_time=lastUpdate, **kwargs)
                connection.execute(insertSt)
                return faceId
        except IntegrityError:
            self.logger.debug(
                "face with attribute {} or face id {} already exist".format(
                    kwargs["attributes_id"] if "attributes_id" in kwargs else "", faceId))
            raise VLException(Error.FaceWithAttributeOrIdAlreadyExist, 409, isCriticalError=False)

    @exceptionWrap
    def updateFace(self, faceId: str, accountId: Optional[str] = None, **kwargs) -> None:
        """
        Update face.

        Args:
            faceId: face id
            accountId: account id

        Keyword Args:
            attribute_id: attribute id
            user_data: face information
            event_id: reference to event which created face
            external_id: external id of the face, if it has its own mapping in external system

        Raises:
            IntegrityError
        """
        try:
            with engine.begin() as connection:

                def updateHistoryLog():
                    query = select([models.ListFace.list_id, models.Face.attributes_id,
                                    models.ListFace.link_key]).where(and_(models.Face.face_id == faceId,
                                                                          models.Face.face_id == models.ListFace.face_id))

                    st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                         models.UnlinkAttributesLog.attributes_id,
                                                                         models.UnlinkAttributesLog.link_key], query)
                    connection.execute(st)

                    lastUpdate = currentTimestamp()
                    updateFaceListSt = update(models.ListFace).where(models.ListFace.face_id == faceId).values(
                        last_update_time=lastUpdate,
                        link_key=LINK_SEQUENCE.next_value())
                    connection.execute(updateFaceListSt)

                if "attributes_id" in kwargs:
                    updateHistoryLog()

                if accountId is None:
                    updateFaceSt = update(models.Face).where(models.Face.face_id == faceId).values(**kwargs)
                else:
                    updateFaceSt = update(models.Face).where(models.Face.face_id == faceId). \
                        where(models.Face.account_id == accountId).values(**kwargs)
                connection.execute(updateFaceSt)

        except IntegrityError:
            self.logger.debug("face with attribute {} already exist".format(kwargs["attributes_id"]))
            raise VLException(Error.FaceWithAttributeOrIdAlreadyExist, 409, isCriticalError=False)

    @exceptionWrap
    def linkFacesToList(self, listId: str, faces: List[str]) -> Tuple[List[str], List[str]]:
        """
        Attach faces to list.

        Args:
            listId: list id
            faces: face ids

        Raises:
            IntegrityError
            Exception

        Returns:
            List of success link faces and failed link faces.
        """
        success = []
        error = []
        lastUpdate = currentTimestamp()

        def linkFace(faceId, conn):

            try:
                updateFaceListSt = insert(models.ListFace).values(list_id=listId, face_id=faceId,
                                                                  last_update_time=lastUpdate)
                conn.execute(updateFaceListSt)
            except IntegrityError:
                return False
            else:
                success.append(faceId)
                return True

        with engine.begin() as connection:
            updateFaceSt = update(models.Face).where(models.Face.face_id.in_(faces)).values(
                last_update_time=lastUpdate)
            connection.execute(updateFaceSt)
            updateListSt = update(models.List).where(models.List.list_id == listId).values(
                last_update_time=lastUpdate)
            connection.execute(updateListSt)

        for face in faces:
            with engine.begin() as connection:
                linkFace(face, connection)

        return success, error

    @exceptionWrap
    def unlinkFacesFromList(self, listId: str, faces: List[str], accountId: Optional[str] = None):
        """
        Unlink faces from list.

        Args:
            listId: list id
            faces: face ids
            accountId: account id
        """
        with engine.begin() as connection:
            lastUpdate = currentTimestamp()

            def updateHistoryLog():
                querySelect = select([models.ListFace.list_id, models.Face.attributes_id,
                                      models.ListFace.link_key]).where(and_(models.Face.face_id.in_(faces),
                                                                            models.Face.face_id == models.ListFace.face_id,
                                                                            models.ListFace.list_id == listId))

                st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                     models.UnlinkAttributesLog.attributes_id,
                                                                     models.UnlinkAttributesLog.link_key], querySelect)

                connection.execute(st)

            def unlinkFaces():
                deleteFacesSt = delete(models.ListFace).where(and_(models.ListFace.face_id.in_(faces),
                                                                   models.ListFace.list_id == listId,
                                                                   models.List.account_id == accountId if accountId is
                                                                                                          not None else True
                                                                   ))
                connection.execute(deleteFacesSt)

                updateListSt = update(models.List).where(models.List.list_id == listId).values(
                    last_update_time=lastUpdate)
                connection.execute(updateListSt)
                updateFaceSt = update(models.Face).where(models.Face.face_id.in_(faces)).values(
                    last_update_time=lastUpdate)
                connection.execute(updateFaceSt)

            updateHistoryLog()
            unlinkFaces()

    @exceptionWrap
    def createList(self, account_id: str, user_data: Optional[str] = "", type: Optional[int] = 0) -> str:
        """
        Create list for account.

        Args:
            type: list type, 1 - persons, 0 - faces
            account_id: account id
            user_data: user data

        Returns:
            list id
        """
        with engine.begin() as connection:
            listId = str(uuid4())
            createTime = currentTimestamp()
            lastUpdate = currentTimestamp()
            insertSt = insert(models.List).values(list_id=listId, account_id=account_id, user_data=user_data,
                                                  type=type, create_time=createTime, last_update_time=lastUpdate)
            connection.execute(insertSt)
            return listId

    @exceptionWrap
    def getFaces(self, eventId: Optional[str] = None, accountId: Optional[str] = None, userData: Optional[str] = None,
                 listId: Optional[str] = None, createTimeLt: Optional[datetime] = None,
                 createTimeGte: Optional[datetime] = None, faceIds: Optional[List[str]] = None, page: Optional[int] = 1,
                 pageSize: Optional[int] = 100, externalId: Optional[str] = None,
                 calculateFaceCount: Optional[int] = 1) -> Tuple[int, List[Dict[str, str]]]:
        """
        Search faces.

        Args:
            eventId: event id
            accountId: account id
            userData: user data
            listId: list id
            createTimeLt: upper bound of face create time
            createTimeGte: lower bound of face create time
            faceIds: face ids
            page: page
            pageSize: page size
            externalId: external id of the face, if it has its own mapping in external system
            calculateFaceCount: flag: 1 - calculates number of faces; 0 - not calculates number of faces and returns -1

        Returns:
            Tuple with count of faces and faces list
        """
        filters = and_(models.Face.account_id == accountId if accountId is not None else True,
                       models.Face.user_data.like("%{}%".format(userData)) if userData is not None else True,
                       models.Face.event_id == eventId if eventId is not None else True,
                       models.Face.create_time < createTimeLt if createTimeLt is not None else True,
                       models.Face.create_time >= createTimeGte if createTimeGte is not None else True,
                       models.Face.external_id == externalId if externalId is not None else True,
                       models.Face.face_id.in_(faceIds) if faceIds is not None else True,
                       models.ListFace.face_id == models.Face.face_id if listId is not None else True,
                       models.ListFace.list_id == listId if listId is not None else True)

        with engine.begin() as connection:

            # speedup for small "get faces by ids" queries: no pagination and no "SELECT count() ..." queries
            onlyOnePage = (faceIds is not None and pageSize >= len(faceIds) and page == 1)

            # all filters and pagination is applied here
            facesQuery = Query(models.Face).filter(filters).order_by(models.Face.create_time.desc()) \
                .offset((page - 1) * pageSize).limit(pageSize).subquery()

            # join with ListFace here
            faceAndListQuery = Query([facesQuery, models.ListFace.list_id]) \
                .outerjoin(models.ListFace, facesQuery.c.face_id == models.ListFace.face_id) \
                .order_by(facesQuery.c.create_time.desc())
            res = connection.execute(faceAndListQuery.statement)
            faceListRows = res.cursor.fetchall()

            def groupFaces(faces: List[List[Any]]) -> List[Dict[str, Union[str, List[str]]]]:
                """
                Make json from raw SQL response.

                Join same faces with different lists.
                e.g.
                    face1 list1 --> face1 [ list1 ]
                    face2 list2 \
                    face2 list3 --> face2 [ list2, list3, list4 ]
                    face2 list4 /
                    face3 None  --> face3 []

                Args:
                    faces: raw sql response

                Returns:
                    result faces
                """
                distinctFaces = []
                distinctFacesIndex = {}
                for face in faces:
                    if face[0] not in distinctFacesIndex:
                        distinctFaces.append({
                            "face_id": face[0], "attributes_id": face[1], "account_id": face[2],
                            "user_data": face[4] if face[4] is not None else "",
                            "create_time": convertTimeToString(face[5], STORAGE_TIME == 'UTC'),
                            "event_id": face[3], "person_id": face[7], "external_id": face[8], "lists": []})
                        distinctFacesIndex[face[0]] = distinctFaces[-1]
                    if face[9] is not None:
                        distinctFacesIndex[face[0]]['lists'].append(face[9])
                return distinctFaces

            groupedFaces = groupFaces(faceListRows)
            faceCount = -1
            if calculateFaceCount:
                if onlyOnePage:
                    faceCount = len(groupedFaces)
                else:
                    query = Query([func.count(models.Face.face_id).label('count')])
                    query = query.filter(filters)
                    res = connection.execute(query.statement)
                    faceCount = res.cursor.fetchone()[0]

            return faceCount, groupedFaces

    @exceptionWrap
    def getLists(self, accountId: Optional[str] = None, userData: Optional[str] = None,
                 listIds: Optional[List[str]] = None, listType: Optional[int] = None, page: Optional[int] = 1,
                 pageSize: Optional[int] = 100) -> Tuple[int, List[Dict[str, str]]]:
        """
        Get list

        Args:
            listType: type of list, 0 -
            listIds: list ids
            accountId: account id
            userData: user data
            page: page
            pageSize: page size

        Returns:
            Tuple, count lists and list with lists
        """
        filters = and_(models.List.account_id == accountId if accountId is not None else True,
                       models.List.user_data.like("%{}%".format(userData)) if userData is not None else True,
                       models.List.type == listType if listType is not None else True,
                       models.List.list_id.in_(listIds) if listIds is not None else True)
        with engine.begin() as connection:
            def getCountOfList():
                query = Query([func.count(models.List.list_id).label('count')])
                query = query.filter(filters)
                res = connection.execute(query.statement)
                return res.cursor.fetchone()[0]

            listCount = getCountOfList()

            def getLists():
                query = Query(models.List)
                query = query.filter(filters).order_by(models.List.create_time.desc()).offset((page - 1) * pageSize). \
                    limit(pageSize).offset((page - 1) * pageSize).limit(pageSize)
                res = connection.execute(query.statement)
                return res.cursor.fetchall()

            listRows = getLists()

            def getCountFacesInNonEmptyList(lists):
                query = Query([models.ListFace.list_id, func.count(models.ListFace.face_id).label('count')])
                query = query.filter(and_(models.ListFace.list_id.in_(lists))).group_by(models.ListFace.list_id)
                res = connection.execute(query.statement)
                listFaceCountRows = res.cursor.fetchall()
                return {list_[0]: list_[1] for list_ in listFaceCountRows}

            def getCountPersonsInNonEmptyList(lists):
                query = Query([models.ListPerson.list_id, func.count(models.ListPerson.person_id).label('count')])
                query = query.filter(and_(models.ListPerson.list_id.in_(lists))).group_by(models.ListPerson.list_id)
                res = connection.execute(query.statement)
                listPersonCountRows = res.cursor.fetchall()
                return {list_[0]: list_[1] for list_ in listPersonCountRows}

            listAndCountFaces = getCountFacesInNonEmptyList([list_[0] for list_ in listRows])
            listAndCountPersons = getCountPersonsInNonEmptyList([list_[0] for list_ in listRows])

            return listCount, [
                {"list_id": list_[0], "user_data": list_[2] if list_[2] is not None else "", "account_id": list_[1],
                 "face_count": listAndCountFaces[list_[0]] if list_[0] in listAndCountFaces else 0,
                 "person_count": listAndCountPersons[list_[0]] if list_[0] in listAndCountPersons else 0,
                 "type": list_[3], 'create_time': convertTimeToString(list_[4], STORAGE_TIME == 'UTC'),
                 'last_update_time': convertTimeToString(list_[5], STORAGE_TIME == "UTC")} for list_ in
                listRows]

    @exceptionWrap
    def getListsWithKeys(self, listIds: List[str]) -> List[Dict[str, str]]:
        """
        Get lists with last link and unlink keys
        Args:
            listIds: list ids

        Returns:
            Tuple with list ids, link and unlink keys
        """
        with engine.begin() as connection:
            queriesMaxLinkKey = []
            queriesMaxUnlinkKey = []
            for listId in listIds:
                queryLinkKey = Query([models.ListFace.list_id, models.ListFace.link_key]).filter(
                    models.ListFace.list_id == listId).order_by(models.ListFace.link_key.desc()).limit(1)
                queriesMaxLinkKey.append(queryLinkKey)

                queryUnlinkKey = Query(
                    [models.UnlinkAttributesLog.list_id, models.UnlinkAttributesLog.unlink_key]).filter(
                    models.UnlinkAttributesLog.list_id == listId).order_by(
                    models.UnlinkAttributesLog.unlink_key.desc()).limit(1)
                queriesMaxUnlinkKey.append(queryUnlinkKey)

            maxLinkKeys = connection.execute(union_all(*queriesMaxLinkKey)).fetchall()
            mapListIdMaxLinkKey = dict(maxLinkKeys)

            maxUnlinkKeys = connection.execute(union_all(*queriesMaxUnlinkKey)).fetchall()
            mapListIdMaxUnlinkKey = dict(maxUnlinkKeys)

            result = [
                {'list_id': listId, 'link_key': mapListIdMaxLinkKey[listId] if listId in mapListIdMaxLinkKey else None,
                 'unlink_key': mapListIdMaxUnlinkKey[listId] if listId in mapListIdMaxUnlinkKey else None} for listId in
                listIds]

            return result

    @exceptionWrap
    def deleteFaces(self, faces: List[str], accountId: Optional[str] = None) -> None:
        """
        Remove faces.

        Args:
            accountId: faces account id
            faces: faces ids
        """
        with engine.begin() as connection:
            def updateHistoryLog():
                query = select([models.ListFace.list_id, models.Face.attributes_id,
                                models.ListFace.link_key]).where(and_(models.Face.face_id.in_(faces),
                                                                      models.Face.face_id == models.ListFace.face_id))

                st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                     models.UnlinkAttributesLog.attributes_id,
                                                                     models.UnlinkAttributesLog.link_key], query)

                connection.execute(st)

                lastUpdate = currentTimestamp()

                updateListSt = update(models.List).where(
                    exists(select([models.List.list_id]).where(and_(models.List.list_id == models.ListFace.list_id,
                                                                    models.ListFace.face_id.in_(faces))))).values(
                    last_update_time=lastUpdate)
                connection.execute(updateListSt)

            deleteFacesSt = delete(models.Face).where(and_(models.Face.face_id.in_(faces),
                                                           models.Face.account_id == accountId if accountId is not None
                                                           else True))
            updateHistoryLog()
            connection.execute(deleteFacesSt)

    @exceptionWrap
    def deleteLists(self, lists: List[str], accountId: Optional[str] = None) -> None:
        """
        Remove lists.

        Args:
            accountId: lists account id
            lists: lists
        """
        with engine.begin() as connection:
            deleteFacesSt = delete(models.List).where(and_(models.List.list_id.in_(lists),
                                                           models.List.account_id == accountId if accountId is not None
                                                           else True))
            connection.execute(deleteFacesSt)

    @exceptionWrap
    def updateListUserData(self, listId: str, userData: str) -> None:
        """
        Update user data of list

        Args:
            listId: list id
            userData: user data
        """
        with engine.begin() as connection:
            lastUpdate = currentTimestamp()

            updateListSt = update(models.List).where(models.List.list_id == listId).values(
                user_data=userData)
            connection.execute(updateListSt)

            updateListSt = update(models.List).where(models.List.list_id == listId).values(last_update_time=lastUpdate)
            connection.execute(updateListSt)

    @exceptionWrap
    def isFaceExist(self, faceId: str, accountId: Optional[str] = None) -> bool:
        """
        Checking to exist face or not.

        Args:
            accountId: account id
            faceId: face id

        Returns:
            true if face exist else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.Face.face_id).label('count')])
            query = query.filter(and_(models.Face.face_id == faceId,
                                      models.Face.account_id == accountId if accountId is not None else True))
            res = connection.execute(query.statement)
            faceCount = res.cursor.fetchone()[0]
            return True if faceCount > 0 else False

    @exceptionWrap
    def isFacesExist(self, faceIds: List[str], accountId: Optional[str] = None) -> bool:
        """
        Checking to exist faces or not.

        Args:
            accountId: account id
            faceIds: face ids

        Returns:
            True if all faces exist else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.Face.face_id).label('count')])
            query = query.filter(models.Face.face_id.in_(faceIds),
                                 models.Face.account_id == accountId if accountId is not None else True)
            res = connection.execute(query.statement)
            faceCount = res.cursor.fetchone()[0]
            return True if faceCount == len(faceIds) else False

    @exceptionWrap
    def isListsExist(self, listIds: List[str], accountId: Optional[str] = None) -> bool:
        """
        Checking to exist lists or not.

        Args:
            accountId: account id
            listIds: list ids

        Returns:
            True if all lists exist else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.List.list_id).label('count')])
            query = query.filter(models.List.list_id.in_(listIds),
                                 models.List.account_id == accountId if accountId is not None else True)
            res = connection.execute(query.statement)
            faceCount = res.cursor.fetchone()[0]
            return True if faceCount == len(listIds) else False

    @exceptionWrap
    def isListExist(self, listId: str, accountId: Optional[str] = None) -> bool:
        """
        Checking to exist list or not

        Args:
            accountId: account id
            listId: list id

        Returns:
            True if list exist else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.List.list_id).label('count')])
            query = query.filter(and_(models.List.list_id == listId,
                                      models.List.account_id == accountId if accountId is not None else True))
            res = connection.execute(query.statement)
            listCount = res.cursor.fetchone()[0]
            return True if listCount > 0 else False

    @exceptionWrap
    def removeFreeFaces(self, timeLt: Optional[datetime] = None, accountId: Optional[str] = None, limit: int = 1000
                        ) -> List[str]:
        """
        Remove not linked faces
        Args:
            timeLt: upper bound of face update time
            accountId: account id
            limit: max count faces for removing
        Returns:
            list with deleted faces' ids
        """
        bounder = timeLt if timeLt else currentTimestamp()
        filters = and_(models.Face.person_id == None, ~exists().where(models.Face.face_id == models.ListFace.face_id),
                       models.Face.last_update_time <= bounder,
                       models.Face.account_id == accountId if accountId else True)
        with engine.begin() as connection:
            facesForRemoving = select([models.Face.face_id]).where(filters).order_by(
                models.Face.last_update_time.asc()).limit(limit)
            deleteSt = delete(models.Face).where(models.Face.face_id.in_(facesForRemoving)).returning(
                models.Face.face_id)
            res = connection.execute(deleteSt).fetchall()
            removedFaceIds = [faceId[0] for faceId in res]

            return removedFaceIds

    @exceptionWrap
    def linkPersonsToList(self, listId: str, persons: List[str]) -> Tuple[List[str], List[str]]:
        """
        Attach persons to list.

        Args:
            listId: list id
            persons: person ids

        Returns:
            List of success link persons and failed link persons
        """
        success = []
        error = []
        lastUpdate = currentTimestamp()
        with engine.begin() as connection:
            updateListSt = update(models.List).where(models.List.list_id == listId).values(
                last_update_time=lastUpdate)
            connection.execute(updateListSt)
        for person in persons:
            try:
                with engine.begin() as connection:
                    updatePersonListSt = insert(models.ListPerson).values(list_id=listId, person_id=person)
                    connection.execute(updatePersonListSt)
                    query = Query([models.Face.face_id, models.Face.attributes_id])
                    query = query.filter(models.Face.person_id == person)
                    res = connection.execute(query.statement).cursor.fetchall()
                    faces = [face[0] for face in res]

                    for face in faces:
                        updateFaceListSt = insert(models.ListFace).values({"list_id": listId, "face_id": face,
                                                                           "last_update_time": lastUpdate,
                                                                           "person_id": person})

                        connection.execute(updateFaceListSt)

                        updateListSt = update(models.List).where(models.List.list_id == listId). \
                            values(last_update_time=lastUpdate)
                        connection.execute(updateListSt)
                        updateFaceSt = update(models.Face).where(models.Face.face_id.in_(faces)).values(
                            last_update_time=lastUpdate)
                        connection.execute(updateFaceSt)

            except IntegrityError as e:
                continue
            except Exception as e:
                error.append(person)
            else:
                success.append(person)
        return success, error

    @exceptionWrap
    def unlinkPersonsFromList(self, listId: str, persons: List[str]) -> None:
        """
        Unlink persons from list.

        Args:
            listId: list id
            persons: person ids
        """
        with engine.begin() as connection:
            lastUpdate = currentTimestamp()

            def updateHistoryLog():
                query = select([models.ListFace.list_id, models.Face.attributes_id,
                                models.ListFace.link_key]).where(and_(models.Face.person_id.in_(persons),
                                                                      models.Face.face_id == models.ListFace.face_id,
                                                                      models.ListFace.list_id == listId))

                st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                     models.UnlinkAttributesLog.attributes_id,
                                                                     models.UnlinkAttributesLog.link_key], query)

                connection.execute(st)

            def unlinkPersons():
                deleteFacesSt = delete(models.ListFace).where(and_(models.ListFace.person_id.in_(persons),
                                                                   models.ListFace.list_id == listId))
                connection.execute(deleteFacesSt)
                deletePersonsSt = delete(models.ListPerson).where(and_(models.ListPerson.person_id.in_(persons),
                                                                       models.ListPerson.list_id == listId))
                connection.execute(deletePersonsSt)
                updateListSt = update(models.List).where(models.List.list_id == listId).values(
                    last_update_time=lastUpdate)
                connection.execute(updateListSt)
                updateFaceSt = update(models.Face).where(models.Face.person_id.in_(persons)).values(
                    last_update_time=lastUpdate)
                connection.execute(updateFaceSt)

            updateHistoryLog()
            unlinkPersons()

    @exceptionWrap
    def createPerson(self, externalPersonId: Optional[str] = None, **kwargs) -> str:
        """
        Create person

        Args:
            externalPersonId (str): external id of the person, if it has its own mapping in external system

        Keyword Args:
            user_data: face information
            account_id: id of account, required
            external_id: external id of the person, if it has its own mapping in external system
        """
        with engine.begin() as connection:
            personId = str(uuid4()) if externalPersonId is None else externalPersonId
            createTime = currentTimestamp()
            insertSt = insert(models.Person).values(person_id=personId, create_time=createTime, **kwargs)
            connection.execute(insertSt)
            return personId

    @exceptionWrap
    def deletePersons(self, persons: List[str], accountId: Optional[str] = None) -> None:
        """
        Remove persons.

        Args:
            accountId: faces account id
            persons: person ids
        """
        with engine.begin() as connection:
            def updateHistoryLog():
                query = select([models.ListFace.list_id, models.Face.attributes_id,
                                models.ListFace.link_key]).where(and_(models.Face.person_id.in_(persons),
                                                                      models.Face.face_id == models.ListFace.face_id))

                st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                     models.UnlinkAttributesLog.attributes_id,
                                                                     models.UnlinkAttributesLog.link_key], query)

                connection.execute(st)

                lastUpdate = currentTimestamp()

                updateListSt = update(models.List).where(
                    exists(select([models.List.list_id]).where(and_(models.List.list_id == models.ListPerson.list_id,
                                                                    models.ListPerson.person_id.in_(persons))))).values(
                    last_update_time=lastUpdate)
                connection.execute(updateListSt)

            def deletePersons():
                deletePersonSt = delete(models.Person).where(and_(models.Person.person_id.in_(persons),
                                                                  models.Person.account_id == accountId if accountId \
                                                                  is not None else True))
                connection.execute(deletePersonSt)
                deletePersonFacesFromListSt = delete(models.ListFace).where(
                    and_(models.ListFace.person_id.in_(persons)))
                connection.execute(deletePersonFacesFromListSt)
                updateFacesSt = update(models.Face).where(models.Face.person_id.in_(persons)).values(
                    person_id=None)
                connection.execute(updateFacesSt)

            updateHistoryLog()
            deletePersons()

    @exceptionWrap
    def isPersonsExist(self, personIds: List[str], accountId: Optional[str] = None) -> bool:
        """
        Checking to exist faces or not.

        Args:
            accountId: account id
            personIds: person ids

        Returns:
            True if all faces exist else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.Person.person_id).label('count')])
            query = query.filter(models.Person.person_id.in_(personIds),
                                 models.Person.account_id == accountId if accountId is not None else True)
            res = connection.execute(query.statement)
            personCount = res.cursor.fetchone()[0]
            return True if personCount == len(personIds) else False

    @exceptionWrap
    def updatePerson(self, personId: str, **kwargs) -> None:
        """
        Update user data of person

        Args:
            personId: person id

        Keyword Args:
            user_data: user data
            external_id: external id of the face, if it has its own mapping in external system
        """
        with engine.begin() as connection:
            updatePersonSt = update(models.Person).where(models.Person.person_id == personId).values(**kwargs)
            connection.execute(updatePersonSt)

    @exceptionWrap
    def linkFaceToPerson(self, personId: str, faceId: str, accountId: str = None) -> None:
        """
        Link face to person.

        Args:
            personId: person id
            faceId: face id
            accountId: account id of the face
        Raises:
            NotUpdatedError if no rows were updated
        """
        with engine.begin() as connection:
            personAlias = aliased(models.Person)
            updateFaceSt = update(models.Face).where(and_(
                models.Face.person_id == None, models.Face.face_id == faceId,
                models.Face.account_id == accountId if accountId is not None else True,
                exists(select([personAlias.person_id]).where(and_(
                    personAlias.person_id == personId,
                    personAlias.account_id == accountId if accountId is not None else True)))
            )).values(person_id=personId)
            updated = connection.execute(updateFaceSt).rowcount
            if not updated:
                raise NotUpdatedError
            lastUpdate = currentTimestamp()
            query = Query(models.ListPerson.list_id)
            query = query.filter(models.ListPerson.person_id == personId)
            res = connection.execute(query.statement)
            lists = [r[0] for r in res.cursor.fetchall()]

            if len(lists) > 0:
                for list_ in lists:
                    updateFaceListSt = insert(models.ListFace).values(
                        {"list_id": list_, "face_id": faceId, "person_id": personId,
                         "last_update_time": lastUpdate})
                    connection.execute(updateFaceListSt)
                    updateListSt = update(models.List).where(models.List.list_id == list_).values(
                        last_update_time=lastUpdate)
                    connection.execute(updateListSt)

                updateFaceSt = update(models.Face).where(models.Face.person_id == personId).values(
                    last_update_time=lastUpdate)
                connection.execute(updateFaceSt)

    @exceptionWrap
    def unlinkFaceFromPerson(self, personId: str, faceId: str, accountId: Optional[str] = None) -> None:
        """
        Unlink face from person.

        Args:
            personId: person id
            faceId: face id
        Raises:
            NotUpdatedError if no rows were updated
        """
        with engine.begin() as connection:
            lastUpdate = currentTimestamp()

            def updateHistoryLog():
                query = select([models.ListFace.list_id, models.Face.attributes_id,
                                models.ListFace.link_key]).where(and_(models.Face.face_id == faceId,
                                                                      models.Face.face_id == models.ListFace.face_id,
                                                                      models.ListFace.person_id == personId))

                st = insert(models.UnlinkAttributesLog).from_select([models.UnlinkAttributesLog.list_id,
                                                                     models.UnlinkAttributesLog.attributes_id,
                                                                     models.UnlinkAttributesLog.link_key], query)

                connection.execute(st)

            def unlinkFace():
                updateFaceSt = update(models.Face).where(and_(
                    models.Face.face_id == faceId, models.Face.person_id == personId,
                    models.Face.account_id == accountId if accountId is not None else True
                )).values(person_id=None)
                updated = connection.execute(updateFaceSt).rowcount
                if not updated:
                    raise NotUpdatedError
                smth = select([models.List.list_id, models.ListFace.list_id]). \
                    where(and_(models.List.list_id == models.ListFace.list_id, models.ListPerson.person_id == personId))
                updateListSt = update(models.List).where(exists(smth)).values(last_update_time=lastUpdate)
                connection.execute(updateListSt)
                deleteFacesSt = delete(models.ListFace).where(and_(models.ListFace.person_id == personId,
                                                                   models.ListFace.face_id == faceId))
                connection.execute(deleteFacesSt)
                updateFaceSt = update(models.Face).where(models.Face.person_id == personId).values(
                    last_update_time=lastUpdate)
                connection.execute(updateFaceSt)

            updateHistoryLog()
            unlinkFace()

    @exceptionWrap
    def getPersons(self, accountId: Optional[str] = None, userData: Optional[str] = None, listId: Optional[str] = None,
                   personIds: Optional[List[str]] = None, faceIds: Optional[List[str]] = None,
                   createTimeLt: Optional[datetime] = None, createTimeGte: Optional[datetime] = None,
                   page: Optional[int] = 1, pageSize: Optional[int] = 100, externalId: Optional[str] = None,
                   calculateFaceCount: Optional[int] = 1) -> Tuple[int, List[Dict[str, str]]]:
        """
        Get list of persons

        Args:
            personIds: person ids
            faceIds: face ids
            listId: list id
            accountId: account id
            userData: user data
            createTimeLt: upper bound of person create time
            createTimeGte: lower bound of person create time
            page: page
            pageSize: page size
            externalId: external id of the person, if it has its own mapping in external system
            calculateFaceCount: flag: 1 - calculates number of faces; 0 - not calculates number of faces and returns -1

        Returns:
            Tuple: first element - person count, second - list with persons
        """
        filters = and_(models.Person.account_id == accountId if accountId is not None else True,
                       models.Person.user_data.like("%{}%".format(userData)) if userData is not None else True,
                       models.Person.person_id.in_(personIds) if personIds is not None else True,
                       and_(models.Face.face_id.in_(faceIds), models.Face.person_id == models.Person.person_id
                            ) if faceIds is not None else True,
                       models.ListPerson.person_id == models.Person.person_id if listId is not None else True,
                       models.ListPerson.list_id == listId if listId is not None else True,
                       models.Person.external_id == externalId if externalId is not None else True,
                       models.Person.create_time < createTimeLt if createTimeLt is not None else True,
                       models.Person.create_time >= createTimeGte if createTimeGte is not None else True,
                       )
        with engine.begin() as connection:
            def getCountOfPersons():
                query = Query([func.count(models.Person.person_id).label('count')])
                query = query.filter(filters)
                res = connection.execute(query.statement)
                return res.cursor.fetchone()[0]

            if calculateFaceCount:
                personCount = getCountOfPersons()
            else:
                personCount = -1

            def getPersons():
                query = Query(models.Person)
                query = query.filter(filters).order_by(
                    models.Person.create_time.desc()).offset((page - 1) * pageSize).limit(pageSize)
                res = connection.execute(query.statement)
                return res.cursor.fetchall()

            def getFacesOfPersons(persons):
                query = Query([models.Face.face_id, models.Face.person_id])
                query = query.filter(models.Face.person_id.in_(persons))
                res = connection.execute(query.statement)
                mapFacePerson = res.cursor.fetchall()
                res = {}
                for face, person in mapFacePerson:
                    if person in res:
                        res[person].append(face)
                    else:
                        res[person] = [face]
                return res

            def getListsOfPersons(persons):
                query = Query([models.ListPerson.list_id, models.ListPerson.person_id])
                query = query.filter(models.ListPerson.person_id.in_(persons))
                res = connection.execute(query.statement)
                mapListPerson = res.cursor.fetchall()
                res = {}
                for lunaList, person in mapListPerson:
                    if person in res:
                        res[person].append(lunaList)
                    else:
                        res[person] = [lunaList]
                return res

            personsRows = getPersons()
            facesOfPerson = getFacesOfPersons([person[0] for person in personsRows])
            listsOfPerson = getListsOfPersons([person[0] for person in personsRows])
            return personCount, [{"person_id": person[0], "account_id": person[1],
                                  "user_data": person[2] if person[2] is not None else "",
                                  "create_time": convertTimeToString(person[3], STORAGE_TIME == 'UTC'),
                                  "external_id": person[4] if person[4] is not None else None,
                                  "faces": facesOfPerson[person[0]] if person[0] in facesOfPerson else [],
                                  "lists": listsOfPerson[person[0]] if person[0] in listsOfPerson else []} for person
                                 in personsRows]

    @exceptionWrap
    def isFaceFree(self, faceId: str, accountId: Optional[str] = None) -> bool:
        """
        Checking is face free or not.

        Args:
            accountId: account id
            faceId: face id

        Returns:
            True if person id is None else false
        """
        with engine.begin() as connection:
            query = Query([func.count(models.Face.face_id).label('count')])
            query = query.filter(and_(models.Face.face_id == faceId,
                                      models.Face.account_id == accountId if accountId is not None else True,
                                      models.Face.person_id == None))
            res = connection.execute(query.statement)
            faceCount = res.cursor.fetchone()[0]
            return True if faceCount > 0 else False

    @exceptionWrap
    def getFacesAttributes(self, facesIds: List[str], accountId: Optional[str] = None
                           ) -> Optional[List[Dict[str, str]]]:
        """
        Return faces attributes id

        Args:
            facesIds: list of faces id
            accountId: account id

        Returns:
            list of attributes id
        """
        query = (Query([models.Face.face_id, models.Face.attributes_id])
                 .filter(and_(models.Face.face_id.in_(facesIds),
                              models.Face.account_id == accountId if accountId is not None else True)))

        with engine.begin() as connection:
            result = connection.execute(query.statement).cursor.fetchall()
            if result:
                return [{'face_id': r[0], 'attributes_id': r[1]} for r in result]
            else:
                return None

    @exceptionWrap
    def getPersonsAttributes(self, personsIds: List[str], accountId: Optional[str] = None
                             ) -> List[Dict[str, list]]:
        """
        Return faces attributes id of persons

        Args:
            personsIds: list of person id
            accountId: account id

        Returns:
            list of persons with all attributes ids
        """
        query = (Query([models.Person.person_id, models.Face.attributes_id])
                 .outerjoin(models.Face, models.Face.person_id == models.Person.person_id)
                 .filter(and_(models.Person.person_id.in_(personsIds),
                              models.Person.account_id == accountId if accountId is not None else True))
                 .order_by(models.Person.person_id))
        personsAttrs = []

        with engine.begin() as connection:
            result = connection.execute(query.statement).cursor.fetchall()

        for personID, attributesID in groupby(result, lambda x: x[0]):
            personsAttrs.append({'person_id': personID, 'attributes_ids': [i[1] for i in attributesID if i[1]]})

        return personsAttrs

    @exceptionWrap
    def getListPlusDelta(self, listId, linkKeyGte: Optional[int] = None, linkKeyLt: Optional[int] = None,
                         limit: int = 10000) -> List[dict]:
        """
        Get attach attributes to lists

        Args:
            listId: list id
            linkKeyLt: upper bound of link key value
            linkKeyGte: lower bound of link key value
            limit: limit

        Returns:
            List of dicts with following keys: "attributes_id", "link_key"
        """

        with engine.begin() as connection:
            filters = and_(models.ListFace.link_key < linkKeyLt if linkKeyLt is not None else True,
                           models.ListFace.link_key >= linkKeyGte if linkKeyGte is not None else True,
                           models.ListFace.list_id == listId,
                           models.Face.attributes_id != None,
                           models.Face.face_id == models.ListFace.face_id)
            query = Query([models.Face.attributes_id, models.ListFace.link_key])
            query = query.filter(filters).order_by(
                models.ListFace.link_key.asc()).limit(limit)
            attributesRows = connection.execute(query.statement).cursor.fetchall()
            res = [dict(zip(("attributes_id", "link_key"), attributesRow)) for attributesRow in attributesRows]

            return res

    @exceptionWrap
    def getListMinusDelta(self, listId, unlinkKeyGte: Optional[int] = None, unlinkKeyLt: Optional[int] = None,
                          limit: int = 10000) -> List[dict]:
        """
        Get history of detach attribute to lists

        Args:
            listId: list id
            unlinkKeyLt: upper bound of unlink key value
            unlinkKeyGte: lower bound of unlink key value
            limit: limit

        Returns:
            List of dicts with following keys: "attributes_id", "link_key", "unlink_key"
        """

        with engine.begin() as connection:
            filters = and_(models.UnlinkAttributesLog.unlink_key < unlinkKeyLt if unlinkKeyLt is not None else True,
                           models.UnlinkAttributesLog.unlink_key >= unlinkKeyGte if unlinkKeyGte is not None else True,
                           models.UnlinkAttributesLog.list_id == listId)
            query = Query([models.UnlinkAttributesLog.attributes_id, models.UnlinkAttributesLog.link_key,
                           models.UnlinkAttributesLog.unlink_key])
            query = query.filter(filters).order_by(
                models.UnlinkAttributesLog.unlink_key.asc()).limit(limit)

            attributesRows = connection.execute(query.statement).cursor.fetchall()
            res = [dict(zip(("attributes_id", "link_key", "unlink_key"), attributesRow)) for attributesRow in
                   attributesRows]

            return res

    @exceptionWrap
    def cleanLog(self, updateTimeLt: Optional[datetime] = None) -> None:
        """
        Remove notes from unlink tables.

        Args:
            updateTimeLt: lower bound of update time

        """
        with engine.begin() as connection:
            cleanLogSt = delete(models.UnlinkAttributesLog).where(
                and_(models.UnlinkAttributesLog.update_time < updateTimeLt if updateTimeLt is not None else True
                     ))
            connection.execute(cleanLogSt)

    @exceptionWrap
    def getAttributes(self, listId: Optional[str] = None, accountId: Optional[str] = None,
                      updateTimeLt: Optional[datetime] = None,
                      updateTimeGte: Optional[datetime] = None, page: Optional[int] = 1,
                      pageSize: Optional[int] = 1000) -> Tuple[int, List[str]]:
        """
        Get attributes by lists.

        Args:
            accountId: account id (if listId is None)
            listId: list id
            updateTimeLt: upper bound of face create time
            updateTimeGte: lower bound of face create time
            page: page
            pageSize: page size

        Returns:
            Tuple with count of attributes and attributes ids list
        """
        if listId is not None:
            filters = and_(models.Face.last_update_time < updateTimeLt if updateTimeLt is not None else True,
                           models.Face.last_update_time >= updateTimeGte if updateTimeGte is not None else True,
                           models.ListFace.face_id == models.Face.face_id if listId is not None else True,
                           models.ListFace.list_id == listId, models.Face.attributes_id != None)
        else:
            filters = and_(models.Face.last_update_time < updateTimeLt if updateTimeLt is not None else True,
                           models.Face.last_update_time >= updateTimeGte if updateTimeGte is not None else True,
                           models.Face.account_id == accountId if accountId is not None else True,
                           models.Face.attributes_id != None)

        with engine.begin() as connection:
            query = Query([func.count(models.Face.attributes_id).label('count')])
            query = query.filter(filters)
            res = connection.execute(query.statement)
            countAttributes = res.cursor.fetchone()[0]
            query = Query(models.Face.attributes_id)
            if listId is not None:
                query = query.filter(filters).order_by(
                    models.ListFace.last_update_time.asc(),
                    models.ListFace.face_id.asc()).offset((page - 1) * pageSize).limit(pageSize)
            else:
                query = query.filter(filters).order_by(
                    models.Face.last_update_time.asc(),
                    models.Face.face_id.asc()).offset((page - 1) * pageSize).limit(pageSize)
            res = connection.execute(query.statement)
            attributesRows = res.cursor.fetchall()
            return countAttributes, [attributesRow[0] for attributesRow in attributesRows]

    @exceptionWrap
    def getPersonIdByFaceId(self, faceId: str, accountId: Optional[str] = None
                            ) -> Union[Tuple[str, Union[str, None]], None]:
        """
        Try to find face_id and person_id by face_id and account_id.

        Args:
            faceId: face id
            accountId: account id

        Returns:
            tuple(faceId, personId) if face found
            None if face not found
        """
        with engine.begin() as connection:
            selectSt = select([models.Face.face_id, models.Face.person_id]).where(and_(
                models.Face.face_id == faceId, models.Face.account_id == accountId if accountId is not None else True))
            res = connection.execute(selectSt).fetchone()
            return res
