from luna3.image_store.image_store import StoreApi
from tornado import gen

LUNA_IMAGE_STORE_ORIGIN = 'http://127.0.0.1:5020'  #: Luna Image Store origin
LUNA_IMAGE_STORE_API_VERSION = 1                   #: Luna Image Store api version
LUNA_IMAGE_STORE_BUCKET = 'warps'                  #: Luna Image Store bucket name

client = StoreApi(LUNA_IMAGE_STORE_ORIGIN, LUNA_IMAGE_STORE_API_VERSION, True)


@gen.coroutine
def get_visionlabs_portrait(portraitId):
    """
    Get portrait from Luna Image Store.
    
    :param portraitId: id of descriptor.
    :rtype: tuple
    :return: * if found image - tuple (imgBytes, True).
             - if not found - tuple(None, False).
    """
    reply = yield client.getImage(LUNA_IMAGE_STORE_BUCKET, portraitId)
    if reply.success:
        return reply.body, True
    return None, False


@gen.coroutine
def save_visionlabs_portrait(imgBytes, faces, isWarpedImage=False):
    """
    Save portrait nowhere.

    :param imgBytes: portrait.
    :param faces:   JSON, with face (see description of extract response).
    :param isWarpedImage: flag that image is warped.
    :return: nothing
    """
    pass


def setup(register_callbacks):
    """
    Registration of a callback.
    
    This function must be called automatically. register_callbacks have one parameter - dict, example \
    *{"save_portrait": save_visionlabs_portrait, "get_portrait": get_visionlabs_portrait}*.
    
    :param register_callbacks: system function for registration callbacks.
    :return: nothing
    """
    register_callbacks({"save_portrait": save_visionlabs_portrait, "get_portrait": get_visionlabs_portrait})
