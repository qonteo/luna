"""
Clients for luna-services.

Attributes:
    FACES_CLIENT (FacesApi): client for luna-faces.
    CORE_CLIENT (CoreAPI): client for luna-core
    CORE_REEXTRACT_CLIENT (CoreAPI): client for re-extract request
    STORE_WARPS_CLIENT (StoreApi): client for image-store with warps
    STORE_PORTRAITS_CLIENT (StoreApi): client for image-store with portraits
"""
from luna3.core.core import CoreAPI
from luna3.faces.faces import FacesApi
from luna3.image_store.image_store import StoreApi
from configs.config import REQUEST_TIMEOUT, CONNECT_TIMEOUT

from configs.config import LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, LUNA_CORE_ORIGIN, LUNA_CORE_API_VERSION, \
    LUNA_CORE_REEXTRACT_ORIGIN, LUNA_CORE_REEXTRACT_API_VERSION, LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN, \
    LUNA_IMAGE_STORE_PORTRAITS_ORIGIN, LUNA_IMAGE_STORE_PORTRAITS_API_VERSION, \
    LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION

FACES_CLIENT = FacesApi(LUNA_FACES_ORIGIN, LUNA_FACES_API_VERSION, asyncRequest=True, requestTimeout=REQUEST_TIMEOUT,
                        connectTimeout=CONNECT_TIMEOUT)
CORE_CLIENT = CoreAPI(LUNA_CORE_ORIGIN, LUNA_CORE_API_VERSION, asyncRequest=True, requestTimeout=REQUEST_TIMEOUT,
                      connectTimeout=CONNECT_TIMEOUT)
CORE_REEXTRACT_CLIENT = CoreAPI(LUNA_CORE_REEXTRACT_ORIGIN, LUNA_CORE_REEXTRACT_API_VERSION, asyncRequest=True,
                                requestTimeout=REQUEST_TIMEOUT, connectTimeout=CONNECT_TIMEOUT)
STORE_WARPS_CLIENT = StoreApi(LUNA_IMAGE_STORE_WARPED_IMAGES_ORIGIN, LUNA_IMAGE_STORE_WARPED_IMAGES_API_VERSION,
                              asyncRequest=True, requestTimeout=REQUEST_TIMEOUT, connectTimeout=CONNECT_TIMEOUT)

STORE_PORTRAITS_CLIENT = StoreApi(LUNA_IMAGE_STORE_PORTRAITS_ORIGIN, LUNA_IMAGE_STORE_PORTRAITS_API_VERSION,
                                  asyncRequest=True, requestTimeout=REQUEST_TIMEOUT, connectTimeout=CONNECT_TIMEOUT)
