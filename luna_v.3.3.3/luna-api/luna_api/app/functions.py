import io
from PIL import Image
from crutches_on_wheels.errors.errors import Error
from configs.config import REQUEST_TIMEOUT, CONNECT_TIMEOUT
from dateutil import parser


def convertDateTime(inputDateTime: str) -> str:
    """
    Function convert time to UTC format if input time format is local

    Args:
        inputDateTime: string with date and time
    Returns:
        string with datetime in UTC, isoformat with 'Z' at the end
    """
    if not str(inputDateTime).endswith('Z'):
        return parser.parse(inputDateTime).replace(tzinfo=None).isoformat('T') + 'Z'
    else:
        return inputDateTime


def checkFormatAndConvertImage(byteImg):
    """
    Check format mimetype and image conversion, if format is not ["image/jpg", "image/jpeg", " image/pjpeg"]
    
    :param byteImg: byte image.
    :return: converted byte image.
    """
    img = Image.open(io.BytesIO(byteImg))
    if img.format == 'JPEG':
        return byteImg
    else:
        output = io.BytesIO()
        img.convert('RGB').save(output, format = 'JPEG')
        return output.getvalue()


def generateStatsTornadoRequestError(reply, statsServer, logger):
    if reply.request_time >= CONNECT_TIMEOUT or reply.request_time >= REQUEST_TIMEOUT:
        if reply.error.message == 'Timeout while connecting':
            return logger.warning("Connection timeout to {}".format(statsServer))
        else:
            return logger.warning("Request timeout to {}".format(statsServer))
    logger.warning("Unknown errror, stats server {}".format(statsServer))


def generateRectISO(detect, landmarks):
    rect = {"height": 0, "width": 0, "x": 0, "y": 0}
    left = landmarks[0]
    right = landmarks[1]

    width = (right[0] - left[0]) / 0.25
    height = width / 0.75

    rect["x"] = int(detect["x"] + round((right[0] + left[0]) / 2, 0) - round(width * 0.5, 0))
    rect["y"] = int(detect["y"] + round((right[1] + left[1]) / 2, 0) - round(width * 0.6, 0))

    rect["width"] = int(round(width, 0))
    rect["height"] = int(round(height, 0))

    return rect
