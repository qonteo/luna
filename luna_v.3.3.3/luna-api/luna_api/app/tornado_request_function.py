import base64
import io
from time import time
from typing import Generator, List

from PIL import Image
from luna3.client import Client
from luna3.common import http_objs
from luna3.common.exceptions import LunaApiException
from tornado import gen

from app.common import SETTER_PORTRAITS_PLUGINS
from app.functions import checkFormatAndConvertImage, generateRectISO
from configs.config import MAX_CANDIDATE_IN_RESPONSE, USE_INDEX_MANAGER, CHECK_INDEX_DELTA
from configs.config import SEND_TO_LUNA_IMAGE_STORE, LUNA_IMAGE_STORE_BUCKET
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from crutches_on_wheels.utils.timer import timer

MAX_PORTRAIT_SIZE = 250


class IndexedLists:
    """
    Singleton indexed lists storage.

    Attributes:
        lastUpdateTime: last update time timestamp
        lists: current lists cache
    """
    lastUpdateTime = 0
    lists = []

    @classmethod
    @gen.coroutine
    def getLists(cls, luna3Client: Client) -> list:
        """
        Get indexed lists' ids.

        Args:
            luna3Client: luna3 Index Manager client
        Returns:
            list of indexed lists' ids
        """
        now = time()
        if now - cls.lastUpdateTime > CHECK_INDEX_DELTA:
            cls.lastUpdateTime = now
            reply = yield luna3Client.lunaIndexManager.getIndexedLists(raiseError=True)
            cls.lists = [l['list_id'] for l in reply.json['lists']]
        return cls.lists


class queryExtractImgParam:
    """
    Structure to save extraction request query parameters.
    """

    def __init__(self):
        self.store = {"estimate_attributes": 0, "estimate_quality": 0, "score_threshold": 0.0, "warped_image": 0,
                      "extract_exif": 0, "extract_descriptor": 1, "estimate_emotions": 0, "estimate_ethnicities": 0,
                      "pitch__lt": 181.0, "yaw__lt": 181.0, "roll__lt": 181.0, "estimate_head_pose": 0}

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __len__(self):
        return len(self.store)

    def getStore(self):
        return self.store

    @property
    def asLuna3Params(self) -> dict:
        """
        Get extract params as kwargs

        Returns:
            dict with keys as kwargs params for luna3.
        """
        param = {"estimateBasicAttributes": self.store["estimate_attributes"],
                 "estimateQuality": self.store["estimate_quality"], "scoreThreshold": self.store["score_threshold"],
                 "warpedImage": self.store["warped_image"], "extractExif": self.store["extract_exif"],
                 "extractDescriptor": self.store["extract_descriptor"],
                 "estimateEmotions": self.store["estimate_emotions"],
                 "estimateEthnicities": self.store["estimate_ethnicities"], "yawThreshold": self.store["yaw__lt"],
                 "pitchThreshold": self.store["pitch__lt"], "rollThreshold": self.store["roll__lt"],
                 "estimateHeadPose": int(self.store["estimate_head_pose"] or
                                           self.store["yaw__lt"] != 181 or
                                           self.store["pitch__lt"] != 181 or
                                           self.store["roll__lt"] != 181)}

        for angle in ("yawThreshold", "pitchThreshold", "rollThreshold"):
            if param[angle] == 181:
                del param[angle]
        return param


class LunaCoreContext:
    """
    Class for requests to luna core.
    Attributes:
        logger: logger
        requestId: request id
        luna3client: luna3 client
    """

    def __init__(self, logger, luna3Client):
        self.logger = logger
        self.luna3client = luna3Client

    @staticmethod
    def convertBodyAndContentTypeFromBase64(body, contentType) -> tuple:
        """
        Convert body from base64 to bytes if need and get correct content content-type.
        Args:
            body: body
            contentType: content type of request

        Returns:
            tuple and content type

        """
        if contentType in ("image/x-jpeg-base64", "application/x-vl-face-descriptor-base64",
                           "application/x-vl-xpk-base64", "image/x-windows-bmp-base64", "image/x-png-base64",
                           "image/x-portable-pixmap-base64", "image/x-bmp-base64", "image/x-tiff-base64",
                           "image/x-gif-base64"):
            partsContentType = contentType.split("/")
            baseType = partsContentType[1]
            if baseType in ("x-windows-bmp-base64", "x-vl-face-descriptor-base64",
                            "x-vl-xpk-base64", "x-portable-pixmap-base64"):
                newBaseType = '-'.join(baseType.split('-')[:-1])
                contentType = partsContentType[0] + "/" + newBaseType
            else:
                newBaseType = '-'.join(baseType.split('-')[1:-1])
                contentType = partsContentType[0] + "/" + newBaseType
            try:
                body = base64.b64decode(body)
            except ValueError:
                raise VLException(Error.ConvertBase64Error, 500, isCriticalError=False)
        return body, contentType

    @timer
    @gen.coroutine
    def aggregateRequestParamAndSendPhotoToLuna(self, body: bytes, requestHeaders: dict,
                                                queryParams: queryExtractImgParam) -> Generator[None, None, dict]:
        """
        Aggregate params and extract descriptors

        Args:
            body: input bytes
            requestHeaders: headers
            queryParams: extract params

        Returns:
            extract result
        Raises:
            VLException: bad params of request
        """
        contentType = requestHeaders.get("Content-Type", None)

        if contentType is None:
            raise VLException(Error.BadContentType, 400)

        body, contentType = LunaCoreContext.convertBodyAndContentTypeFromBase64(body, contentType)

        if contentType in ("image/jpeg", "application/x-vl-face-descriptor", "application/x-vl-xpk"):
            headers = {"Content-Type": contentType}
        elif contentType in ("image/png", "image/x-portable-pixmap", "image/bmp", "image/tiff", "image/gif",
                             "image/x-windows-bmp"):
            try:
                body = checkFormatAndConvertImage(body)
            except Exception:
                raise VLException(Error.ConvertImageToJPGError, 400, isCriticalError=False)

            headers = {"Content-Type": "image/jpeg"}
        else:
            raise VLException(Error.BadContentType, 400, False)

        resLuna = yield self.sendPhotoToLuna(body, headers, queryParams)
        return resLuna

    def mimicryCore12(self, inputJson: dict, queryParams: queryExtractImgParam) -> dict:
        """
        Mimicry extract reply from core to  extract of version 12.
        Args:
            inputJson:  output extract reply
            queryParams: extract params

        Returns:
            extract result as core version 12
        Raises:
            VLException: if extract is failed

        """
        if len(inputJson['failed_images']) > 0:
            repJson = inputJson['failed_images'][0]["error"]
            errorCount = repJson["error"]
            error = Error.formatError(Error.getErrorByErrorCode(errorCount), repJson["detail"])

            self.logger.debug(repJson["detail"])
            raise VLException(Error.generateError(error, error.description + ". Detail: " +
                                                  repJson["detail"]), 400, isCriticalError=False)
        repJson = inputJson['succeeded_images'][0]
        if "file_name" in repJson:
            del repJson["file_name"]

        if "faces" not in repJson:
            error = Error.getErrorByErrorCode(11027)
            raise VLException(Error.generateError(error, error.description + ". Detail: " +
                                                  "No faces found."), 500, isCriticalError=False)
        faces = [face for face in repJson["faces"] if "id" in face or queryParams["extract_descriptor"] == 0]

        if len(faces) == 0:
            # bad quality
            if queryParams["extract_descriptor"] == 1 and (
                    len(repJson["faces"]) > 0 or (queryParams["warped_image"] == 1) and
                    (queryParams["score_threshold"] > 0 or queryParams["pitch__lt"] < 180 or
                     queryParams["yaw__lt"] < 180 or queryParams["roll__lt"] < 180)):
                error = Error.getErrorByErrorCode(11027)
                statusCode = 400
            # face not found
            else:
                statusCode = 500
                error = Error.getErrorByErrorCode(4003)
            raise VLException(Error.generateError(error, error.description + ". Detail: " +
                                                  "No faces found."), statusCode, isCriticalError=False)

        repJson["faces"] = faces

        def mimcryAttributes(face):
            if "landmarks5" in face:
                face["rectISO"] = generateRectISO(face["rect"], face["landmarks5"])
                del face["landmarks5"]
            if "url" in face:
                del face["url"]
            if "attributes" in face:
                attributes = [{"outputName": "attributes", "value": None, "inputName": "basic_attributes"},
                              {"outputName": "ethnicities", "value": None, "inputName": "ethnicities"},
                              {"outputName": "emotions", "value": None, "inputName": "emotions"},
                              {"outputName": "head_pose", "value": None, "inputName": "head_pose"}]

                for attribute in attributes:
                    if attribute["inputName"] in face["attributes"]:
                        attribute["value"] = face["attributes"][attribute["inputName"]]
                newAttributes = {}
                for attribute in attributes:
                    if attribute["value"] is not None:
                        if attribute["outputName"] == "attributes":
                            newAttributes.update(attribute["value"])
                        else:
                            newAttributes[attribute["outputName"]] = attribute["value"]
                face["attributes"] = newAttributes
            return face

        for faceNumber in range(len((repJson["faces"]))):
            repJson["faces"][faceNumber] = mimcryAttributes(repJson["faces"][faceNumber])

        return repJson

    @timer
    @gen.coroutine
    def sendPhotoToLuna(self, binBody: bytes, headers: dict,
                        queryParams: queryExtractImgParam) -> Generator[None, None, dict]:
        """
        Extract

        Args:
            binBody: input bytes
            headers: headers
            queryParams: extract params

        Returns:
            extract result

        Raises:
            VLException(Error.UnknownError, 500): in the case any exceptions except VLException, LunaApiException.
        """
        try:
            if headers["Content-Type"] in ("application/x-vl-face-descriptor", "application/x-vl-xpk"):
                response = yield self.luna3client.lunaCore.uploadDescriptor(descriptorInBytes=binBody, raiseError=True,
                                                                            contentType=headers["Content-Type"])
            else:
                img = http_objs.Image("", body=binBody, mimetype=headers["Content-Type"])
                response = yield self.luna3client.lunaCore.extractDescriptor(img, raiseError=True,
                                                                             **queryParams.asLuna3Params)

            repJson = response.json
            repJson = self.mimicryCore12(repJson, queryParams)

            if headers["Content-Type"] == "image/jpeg" and int(queryParams["extract_descriptor"]) > 0:
                if SEND_TO_LUNA_IMAGE_STORE:
                    yield self.putPortraitsInLunaImageStore(binBody,
                                                            repJson["faces"],
                                                            bool(queryParams["warped_image"]))
                try:
                    for plugin in SETTER_PORTRAITS_PLUGINS:
                        yield plugin(binBody, repJson["faces"], queryParams["warped_image"])
                except Exception:
                    self.logger.exception()
                    raise VLException(Error.ErrorSavePortraitPlugin, 500)
            return repJson

        except (VLException, LunaApiException) as e:
            raise
        except Exception as e:
            self.logger.exception()
            raise VLException(Error.UnknownError, 500)

    @timer
    @gen.coroutine
    def match(self, templatePhotoId: str, candidates: List[str], candidateIsLists: bool = True,
              limit: int = MAX_CANDIDATE_IN_RESPONSE) -> Generator[None, None, dict]:
        """
        Function that realizes matching request.

        Args:
            templatePhotoId: Template candidate (photo id)
            candidates: list of candidates or list set from LUNA
            candidateIsLists: list type (descriptors list or list set)
            limit: reply limit
        Returns:
            In case of success, system returns dict with json from LUNA and status code.
        """

        matchKwargs = {"reference": str(templatePhotoId)}

        if candidateIsLists:
            matchKwargs["lists"] = candidates
            if USE_INDEX_MANAGER:
                indexedLists = yield IndexedLists.getLists(self.luna3client)
                matchKwargs['indexed'] = candidates[0] in indexedLists
        else:
            matchKwargs["candidates"] = candidates

        response = yield self.luna3client.lunaCore.match(**matchKwargs, limit=limit,
                                                         raiseError=True)
        return response.json

    @timer
    @gen.coroutine
    def removeListsFromLuna(self, lists: List[str]) -> Generator[None, None, None]:
        """
        Function that realizes list deletion in LUNA.
        Args:
            lists: list of all list ids in LUNA
        """
        if len(lists) == 0:
            return
        yield self.luna3client.lunaCore.deleteList(listIds=lists, raiseError=True)

    @timer
    @gen.coroutine
    def patchLunaLists(self, patchData: List, mode: str) -> Generator[None, None, None]:
        """
        Function that realizes list modification in LUNA.
        Args:
            patchData: list of pairs (first element in pair is list of descriptor ids, second one is list id/
            mode: list modification mode
        """
        try:
            for data in patchData:
                if mode == "patch":
                    yield self.luna3client.lunaCore.appendList(listId=data[1], data=data[0], raiseError=True)
                else:
                    yield self.luna3client.lunaCore.appendList(listId=data[1], data=data[0], raiseError=True)
        except Exception:
            self.logger.exception()
            raise VLException(Error.UnknownError, 500)

    @staticmethod
    def getFaceFromImg(byteImg: bytes, coord: dict) -> bytes:
        """
        Function that realizes cropping of portrait from photo by detection coordinates.

        Args:
            byteImg: input image, byte type

            coord: detection coordinates
        Returns:
            portrait
        """
        img = Image.open(io.BytesIO(byteImg))

        cropImg = img.crop((coord["left"], coord["bottom"], coord["right"], coord["top"]))
        width, height = cropImg.size
        ratio = min(MAX_PORTRAIT_SIZE / width, MAX_PORTRAIT_SIZE / height)
        size = int(width * ratio), int(height * ratio)
        resizeImg = cropImg.resize(size, Image.BILINEAR)
        output = io.BytesIO()
        resizeImg.save(output, format='JPEG')
        return output.getvalue()

    @staticmethod
    def getCoordOfFace(replyJson: dict) -> dict:
        """
        Receive coordinates from detection.

        Args:
            replyJson:  JSON from LUNA after description detection.
        Returns:
            dictionary with fields left, right, bottom, top.
        """
        strRect = replyJson["rectISO"]
        coord = {"left": max(strRect["x"], 0), "right": (strRect["x"] + strRect["width"]),
                 "bottom": max(strRect["y"], 0),
                 "top": strRect["y"] + strRect["height"]}
        return coord

    @timer
    @gen.coroutine
    def putPortraitsInLunaImageStore(self, imgBytes: bytes, extractFacesJSON: List,
                                     isWarpImage: bool = False) -> Generator[None, None, None]:
        """
        Addition of portraits, which were extracted in LUNA, to luna-image-store.

        Args:
            imgBytes: image bytes.
            extractFacesJSON: JSON from LUNA with all extracted faces.
            isWarpImage: flag, which indicates whether image was warped or not.
        """

        for face in extractFacesJSON:
            if not isWarpImage:
                coord = LunaCoreContext.getCoordOfFace(face)
                img = LunaCoreContext.getFaceFromImg(imgBytes, coord)
            else:
                img = imgBytes

            yield self.luna3client.lunaImageStore.putImage(img, face["id"], LUNA_IMAGE_STORE_BUCKET,
                                                           createThumbnails=1, raiseError=True)

    @timer
    @gen.coroutine
    def getPortraitsFromLunaImageStore(self, photoId: str, requestId: str) -> Generator[None, None, bytes]:
        """
        Receive portrait from luna-image-store.

        Args:

            photoId: descriptor id, whose portrait we get.
            requestId: id of request

        Returns:
            return portraits in bytes
        """
        reply = yield self.luna3client.lunaImageStore.getImage(LUNA_IMAGE_STORE_BUCKET, photoId,
                                                               lunaRequestId=requestId, raiseError=True)
        return reply.body

    @gen.coroutine
    def getLunaVersion(self) -> Generator[None, None, dict]:
        """
        Get version of LUNA Core

        Returns:
            version of luna core
        """
        response = yield self.luna3client.lunaCore.getVersion(raiseError=True)
        return response.json
