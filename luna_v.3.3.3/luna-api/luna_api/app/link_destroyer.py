from tornado import gen

from crutches_on_wheels.utils.timer import timer


@timer
@gen.coroutine
def deleteLinkObjectList(object_id, listId, dbContext, lunaContext) -> None:
    """
    Function that realizes object detach from list.

    :param object_id: object id (person or descriptor)
    :param listId: list id.
    :param lunaContext: luna core context
    :param dbContext: postgres context
    """

    lists = dbContext.getDescriptorsAndLunaListOfObject(object_id, listId)
    dataToRemove = []
    for listDescriptorsPair in lists:
        listIds = dbContext.getAllDescriptorsInLunaList(listDescriptorsPair[0])
        for descriptors in listDescriptorsPair[1]:
            listIds.remove(descriptors)
        dataToRemove.append((listIds, listDescriptorsPair[0]))
    yield lunaContext.patchLunaLists(dataToRemove, "put")
    dbContext.detachObjectFromAccountList(object_id, listId)


@timer
@gen.coroutine
def deleteLinkPersonPhoto(photoId, accountId, personId, dbContext, lunaContext) -> None:
    """
    Delete link between person and descriptor.


    :param photoId: descriptor id
    :param accountId: account id
    :param personId: person id
    :param lunaContext: luna core context
    :param dbContext: postgres context
    """
    lists = dbContext.getAllLunaListWithDescriptor(photoId, personId)
    dataToRemove = []
    for lunaList in lists:
        listId = dbContext.getAllDescriptorsInLunaList(lunaList)
        listId.remove(photoId)
        dataToRemove.append((listId, lunaList))
    yield lunaContext.patchLunaLists(dataToRemove, "put")
    dbContext.detachPhotoFromPerson(photoId, accountId, personId)
