from crutches_on_wheels.errors.errors import Error
from tests.classes import TestBase, authStr
from tests.config import LUNA_IMAGE_STORE_OFF

import unittest

from tests.resources import onePersonList, severalFaces, noFaces, lowImageSize, largeImageSize, moreThan64Faces
from tests.resources import rawDescriptor, xpkFile, warpedImage, standardImage, differentFormatList, base64Files
from tests import luna_api_functions


class TestImage(TestBase):
    """
    Test extract descriptor
    """
    def setUp(self):
        self.createAccountAndToken()

    def test_descriptor_extract_descriptor(self):
        """
        .. test:: test_descriptor_extract_descriptor

            :resources: "/storage/descriptors"
            :description: success extract descriptor
            :LIS: No
            :tag: Descriptor
        """
        @self.authorization
        def extractPhotoTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            for image in onePersonList:
                replyInfo = luna_api_functions.extractDescriptors(headers, filename=image)
                self.assertSuccessExtractPhoto(replyInfo, authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_several_descriptors_from_file(self):
        """
        .. test:: test_descriptor_extract_several_descriptors_from_file

            :resources: "/storage/descriptors"
            :description: success extract all descriptors from one file (9 faces)
            :LIS: No
            :tag: Descriptor
        """
        @self.authorization
        def extractSeveralFaces(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=severalFaces)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            self.assertEqual(len(replyInfo.body['faces']), 9)

        extractSeveralFaces()

    def test_descriptor_extract_maximum_descriptors_from_file(self):
        """
        .. test:: test_descriptor_extract_maximum_descriptors_from_file

            :resources: "/storage/descriptors"
            :description: success extract 64 descriptors from one file (64+ faces on image)
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractMaximumFacesCount(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=moreThan64Faces, requestTimeOut = 60)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            self.assertEqual(len(replyInfo.body['faces']), 64)

        extractMaximumFacesCount()

    def test_descriptor_extract_no_descriptors(self):
        """
        .. test:: test_descriptor_extract_no_descriptors

            :resources: "/storage/descriptors"
            :description: failed extract descriptor while no descriptors in image (0 faces)
            :LIS: No
            :tag: Descriptor
        """
        @self.authorization
        def extractNoFaces(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=noFaces)
            self.assertEqual(replyInfo.statusCode, 500, auth)
            self.assertEqual(replyInfo.body["error_code"], 4003, auth)
            self.assertEqual(replyInfo.body["detail"], "No faces found. Detail: No faces found.", auth)

        extractNoFaces()

    def test_descriptor_extract_low_image_size(self):
        """
        .. test:: test_descriptor_extract_low_image_size

            :resources: "/storage/descriptors"
            :description: failed extract descriptor while image has low size (less than 96x96)
            :LIS: No
            :tag: Descriptor
        """
        @self.authorization
        def extractLowImageSize(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=lowImageSize)
            self.assertEqual(replyInfo.statusCode, 400, auth)
            self.assertEqual(replyInfo.body["error_code"], 3002, auth)
            self.assertEqual(replyInfo.body["detail"],
                "Incorrect image size. Detail: Image size (95x95) is lower than minimum allowed (96x96).", auth)

        extractLowImageSize()

    def test_descriptor_extract_large_image_size(self):
        """
        .. test:: test_descriptor_extract_large_image_size

            :resources: "/storage/descriptors"
            :description: failed extract descriptor while image has large size (more than 4096x4096)
            :LIS: No
            :tag: Descriptor
        """
        @self.authorization
        def extractLargeImageSize(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=largeImageSize)
            self.assertEqual(replyInfo.statusCode, 400, auth)
            self.assertEqual(replyInfo.body["error_code"], 3002, auth)
            self.assertEqual(replyInfo.body["detail"],
                "Incorrect image size. Detail: Image size (4100x2306) is greater than maximum allowed (4096x4096).",
                auth)

        extractLargeImageSize()

    @unittest.skipIf(LUNA_IMAGE_STORE_OFF, "S3 in LUNA API OFF")
    def test_descriptor_extract_descriptor_from_warped_image(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_warped_image

            :resources: "/storage/descriptors"
            :description: success extract descriptor from warp image, check saving portrait is equal to source img
            :tag: Descriptor
            :LIS: Yes
        """
        @self.authorization
        def extractWarpImage(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=warpedImage, warpedImage=True)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            photoId = replyInfo.body['faces'][0]["id"]
            reply = luna_api_functions.getPortrait(headers, photoId)
            with open(warpedImage, "rb") as f:
                imgBytes = f.read()
            self.assertEqual(imgBytes, reply.body, authStr(auth))

        extractWarpImage()

    def test_descriptor_extract_descriptor_from_descriptor(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_descriptor

            :resources: "/storage/descriptors"
            :description: success extract descriptor from raw descriptor
            :tag: Descriptor
            :LIS: No
        """
        @self.authorization
        def extractSendDescriptor(headers, auth):
            with open(rawDescriptor["image"], "rb") as f:
                descriptor = f.read()
            replyInfo = luna_api_functions.extractDescriptors(headers, body = descriptor)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))

        extractSendDescriptor()

    def test_descriptor_extract_descriptor_from_xpk(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_xpk

            :resources: "/storage/descriptors"
            :description: success extract descriptor from xpk file
            :tag: Descriptor
            :LIS: No
        """
        @self.authorization
        def extractSendXpk(headers, auth):
            with open(xpkFile["image"], "rb") as f:
                descriptor = f.read()
            replyInfo = luna_api_functions.extractDescriptors(headers, body = descriptor)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))

        extractSendXpk()

    def test_descriptor_extract_descriptor_from_base64(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_base64

            :resources: "/storage/descriptors"
            :description: success extract descriptors  from data in base64 encoding
            :tag: Descriptor
            :LIS: No
        """
        @self.authorization
        def extractSendBase64(headers, auth):
            for base64File in base64Files:
                with open(base64File["filename"], "rb") as f:
                    descriptor = f.read()
                replyInfo = luna_api_functions.extractDescriptors(headers, body=descriptor,
                                                                  contentType=base64File["Content-Type"])
                self.assertSuccessExtractPhoto(replyInfo, authStr(auth))

        extractSendBase64()

    def test_descriptor_extract_descriptor_with_corrupted_image(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_corrupted_image

            :resources: "/storage/descriptors"
            :description: trying extract descriptors  from data in base64 encoding and content-type  "image/bmp"
            :tag: Descriptor
            :LIS: No
        """
        @self.authorization
        def extractSendBase64WithWrongContentTypeHeader(headers, auth):

            with open(base64Files[0]["filename"], "rb") as f:
                descriptor = f.read()
            replyInfo = luna_api_functions.extractDescriptors(headers, body=descriptor, contentType='image/bmp')
            self.assertErrorRestAnswer(replyInfo, 400, Error.ConvertImageToJPGError, auth = authStr(auth))

        extractSendBase64WithWrongContentTypeHeader()

    def test_descriptor_extract_descriptor_from_base64_bad_base64(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_base64_bad_base64

            :resources: "/storage/descriptors"
            :description: trying extract descriptors  from data in non base64
            :tag: Descriptor
            :LIS: No
        """
        @self.authorization
        def extractSendBase64(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, body=b'123',
                                                              contentType="image/x-jpeg-base64")
            self.assertErrorRestAnswer(replyInfo, 500, Error.ConvertBase64Error, auth = authStr(auth))

        extractSendBase64()

    @unittest.skipIf(LUNA_IMAGE_STORE_OFF, "S3 in LUNA API OFF")
    def test_descriptor_get_portrait(self):
        """
        .. test:: test_descriptor_get_portrait

            :resources: "/storage/portraits/\{descriptor_id\}"
            :description: success getting portrait
            :tag: Descriptor
            :LIS: Yes
        """
        @self.authorization
        def getPortraitsTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            photoId = replyInfo.body['faces'][0]["id"]
            reply = luna_api_functions.getPortrait(headers, photoId)
            self.assertEqual(reply.statusCode, 200, authStr(auth))

        getPortraitsTest()

    def test_descriptor_extract_descriptor_from_non_jpeg_files(self):
        """
        .. test:: test_descriptor_extract_descriptor_from_non_jpeg_files

            :resources: "/storage/descriptors"
            :description: success extract descriptor from non jpg-files
            :tag: Descriptor
            :LIS: No
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            for data in differentFormatList:
                replyInfo = luna_api_functions.extractDescriptors(headers, filename=data["image"])
                self.assertSuccessExtractPhoto(replyInfo, authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_with_bad_content_type(self):
        """
        .. test:: test_descriptor_extract_with_bad_content_type

            :resources: "/storage/descriptors"
            :description: try extracting descriptor with  unsupported Content-Type ("image/jpg")
            :tag: Descriptor
            :LIS: No
        """

        @self.authorization
        def extractPhotoBadContentTypeTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage, contentType="image/jpg")
            self.assertEqual(replyInfo.statusCode, 400, authStr(auth))
            self.assertErrorRestAnswer(replyInfo, 400, Error.BadContentType, auth = authStr(auth))

        extractPhotoBadContentTypeTest()
