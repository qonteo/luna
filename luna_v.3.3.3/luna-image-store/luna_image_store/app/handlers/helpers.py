import ujson as json
from typing import Optional

from image.image import checkFormatAndConvertImage
from configs import config


def getThumbnails(value: str) -> int:
    """
    Thumbnails getter.

    Args:
        value: query param

    Returns:
        int(value)
    Raises:
        ValueError: if value is not int or not in (0, 1).
    """
    createThumbnails = int(value)
    if createThumbnails not in (0, 1):
        raise ValueError
    return createThumbnails


def isCacheable(image_size: int, max_size: int = config.MAX_CACHEABLE_SIZE,
                global_param: bool = config.CACHE_ENABLED) -> bool:
    return global_param and image_size < max_size


def isCorrectContentType(contentType: str) -> bool:
    return contentType in ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/gif', 'image/x-portable-pixmap']


def isCorrectTextContentType(contentType: str) -> bool:
    return contentType in ('application/json', 'text/plain')


def convertImageToJPG(image: bytes) -> Optional[bytes]:
    try:
        return checkFormatAndConvertImage(image)
    except Exception:
        return None


def isJson(body: bytes) -> bool:
    try:
        json.loads(body)
    except ValueError:
        return False
    return True


def matchContentType(contentType: str, body: bytes) -> bool:
    if contentType == 'application/json':
        try:
            json.loads(body)
        except ValueError:
            return False
    elif contentType == 'text/plain':
        try:
            body.decode()
        except ValueError:
            return False
    else:
        return False
    return True
