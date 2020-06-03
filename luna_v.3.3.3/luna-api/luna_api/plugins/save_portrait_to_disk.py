import PIL
from PIL import Image
import os
import io

from tornado import gen

LOCATION = "./portraits"                                        #: root of storage for saving portraits
MAX_PORTRAIT_SIZE = 250


def getCoordOfFace(jsonWithFace):
    """
    Getting of coordinates of face on source image

    :param jsonWithFace:  JSON, with face (see description of extract response).

    :rtype: dict

    :return: dictionary with keys: left, right, bottom, top.
    """
    strRect = jsonWithFace["rectISO"]
    coord = {"left": max(strRect["x"], 0), "right": (strRect["x"] + strRect["width"]), "bottom": max(strRect["y"], 0),
             "top": strRect["y"] + strRect["height"]}
    return coord


def getFaceFromImg(byteImg, coord):
    """
    Extract face from source image  by coordinates.

    :param byteImg: source image, bytes

    :param coord: coordinates of portrait

    :rtype: bytes

    :return: image  with mime/type: image/jpeg
    """
    img = Image.open(io.BytesIO(byteImg))

    cropImg = img.crop((coord["left"], coord["bottom"], coord["right"], coord["top"]))
    width, height = cropImg.size
    ratio = min(MAX_PORTRAIT_SIZE / width, MAX_PORTRAIT_SIZE / height)
    size = int(width * ratio), int(height * ratio)
    resizeImg = cropImg.resize(size, PIL.Image.BILINEAR)
    output = io.BytesIO()
    resizeImg.save(output, format = 'JPEG')
    return output.getvalue()


def getPath(descriptorId):
    """
    Getting path to folder with image.
    
    If you work in *unix system in one folder must be <50k files.
    
    :param descriptorId: id of descriptors
    :return: return string *LOCATION + "/" + descriptorId[-2:] + "/"*
    """
    path = LOCATION + "/" + descriptorId[-2:] + "/"
    return path


@gen.coroutine
def save_visionlabs_portrait(imgBytes, faces, isWarpedImage=False):
    """
    Saving portrait to file.
    
    :param imgBytes: portrait.
    :param faces:   JSON, with face (see description of extract response).
    :param isWarpedImage: flag that image is warped.
    :return: nothing
    """
    for face in faces:
        if not isWarpedImage:
            coord = getCoordOfFace(face)
            img = getFaceFromImg(imgBytes, coord)
        else:
            img = imgBytes
        path = getPath(face["id"])
        if not os.path.exists(path):
            os.makedirs(path)
        f = open(path + face["id"] + ".jpg", 'wb')
        f.write(img)
        f.close()


@gen.coroutine
def get_visionlabs_portrait(portraitId):
    """
    Get portrait from disk.
    
    :param portraitId: id of descriptor.
    :rtype: tuple
    :return: * if found image - tuple (imgBytes, True).
             - if not found - tuple(None, False).
    """
    path = getPath(portraitId)
    pathToImg = path + "/" + portraitId + ".jpg"
    if os.path.isfile(pathToImg):
        with open(pathToImg, "rb") as f:
            imgBytes = f.read()
        return (imgBytes, True)
    else:
        return (None, False)


def setup(register_callbacks):
    """
    Registration of callbacks.
    
    This function must be call automatically. register_callbacks have one parameter - dict, example \
    *{"save_portrait": save_visionlabs_portrait, "get_portrait": get_visionlabs_portrait}*.
    
    :param register_callbacks: system function for registration callbacks.
    :return: nothing
    """
    register_callbacks({"save_portrait": save_visionlabs_portrait, "get_portrait": get_visionlabs_portrait})

