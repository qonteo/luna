from tests.classes import TestBase, authStr
from tests import luna_api_functions
from tests.resources import standardImage, severalFaces, exifWarpedImage, sunGlassesImage, glassesImage
from crutches_on_wheels.errors.errors import Error
import unittest


class TestImageWithQueries(TestBase):
    """
    Test extract descriptor with different query params
    """

    def setUp(self):
        self.createAccountAndToken()

    def test_descriptor_extract_descriptor_with_attributes(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_attributes

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate attributes
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (0, 1)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                                      estimateAttributes=True,
                                                                      extractDescriptor=extractDescriptor)
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertIn('age', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    self.assertIn('eyeglasses', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    self.assertIn('gender', replyInfo.body['faces'][0]['attributes'], authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_emotions(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_emotions

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate emotions
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (0, 1)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                                      estimateAttributes=True,
                                                                      estimateEmotions=True,
                                                                      extractDescriptor=extractDescriptor)
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertIn('emotions', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    self.assertIn('predominant_emotion', replyInfo.body['faces'][0]['attributes']['emotions'],
                                  authStr(auth))
                    self.assertEqual(replyInfo.body['faces'][0]['attributes']['emotions']['predominant_emotion'],
                                     'neutral',
                                     authStr(auth))
                    self.assertIn('estimations', replyInfo.body['faces'][0]['attributes']['emotions'], authStr(auth))
                    estimations = replyInfo.body['faces'][0]['attributes']['emotions']['estimations']
                    emotions = ['anger', 'disgust', 'fear', 'happiness', 'neutral', 'sadness', 'surprise']
                    for emotion in emotions:
                        self.assertIn(emotion, estimations, authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_emotions_and_attributes(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_emotions_and_attributes

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate emotions and attributes
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                              estimateAttributes=True,
                                                              estimateEmotions=True)
            self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))

            self.assertIn('age', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('eyeglasses', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('gender', replyInfo.body['faces'][0]['attributes'], authStr(auth))

            self.assertIn('emotions', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('predominant_emotion', replyInfo.body['faces'][0]['attributes']['emotions'],
                          authStr(auth))
            self.assertEqual(replyInfo.body['faces'][0]['attributes']['emotions']['predominant_emotion'], 'neutral',
                             authStr(auth))
            self.assertIn('estimations', replyInfo.body['faces'][0]['attributes']['emotions'], authStr(auth))
            estimations = replyInfo.body['faces'][0]['attributes']['emotions']['estimations']
            emotions = ['anger', 'disgust', 'fear', 'happiness', 'neutral', 'sadness', 'surprise']
            for emotion in emotions:
                self.assertIn(emotion, estimations, authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_ethnicities(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_ethnicities

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate ethnicities
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (False, True)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                                      estimateAttributes=True,
                                                                      estimateEthnicities=True,
                                                                      extractDescriptor=extractDescriptor)
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertIn('ethnicities', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    self.assertIn('predominant_ethnicity', replyInfo.body['faces'][0]['attributes']['ethnicities'],
                                  authStr(auth))

                    self.assertIn('estimations', replyInfo.body['faces'][0]['attributes']['ethnicities'], authStr(auth))
                    estimations = replyInfo.body['faces'][0]['attributes']['ethnicities']['estimations']
                    ethnicities = ['asian', 'indian', 'caucasian', 'african_american']

                    for ethnicity in ethnicities:
                        self.assertIn(ethnicity, estimations, authStr(auth))

                    self.assertEqual(replyInfo.body['faces'][0]['attributes']['ethnicities']["predominant_ethnicity"],
                                     'caucasian', authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_ethnicities_and_attributes(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_ethnicities_and_attributes

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate ethnicities and attributes
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                              estimateAttributes=True,
                                                              estimateEthnicities=True)
            self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))

            self.assertIn('age', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('eyeglasses', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('gender', replyInfo.body['faces'][0]['attributes'], authStr(auth))

            self.assertIn('ethnicities', replyInfo.body['faces'][0]['attributes'], authStr(auth))
            self.assertIn('predominant_ethnicity', replyInfo.body['faces'][0]['attributes']['ethnicities'],
                          authStr(auth))
            self.assertEqual(replyInfo.body['faces'][0]['attributes']['ethnicities']['predominant_ethnicity'],
                             'caucasian', authStr(auth))
            self.assertIn('estimations', replyInfo.body['faces'][0]['attributes']['ethnicities'], authStr(auth))
            estimations = replyInfo.body['faces'][0]['attributes']['ethnicities']['estimations']
            ethnicities = ['asian', 'indian', 'caucasian', 'african_american']
            for ethnicity in ethnicities:
                self.assertIn(ethnicity, estimations, authStr(auth))

            self.assertEqual(replyInfo.body['faces'][0]['attributes']['ethnicities']["predominant_ethnicity"],
                             'caucasian', authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_glasses(self):
        """
        .. test:: test_descriptor_extract_glasses

            :resources: "/storage/descriptors"
            :description: success extract estimate glasses for different photos
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            cases = {standardImage: 0, sunGlassesImage: 1, glassesImage: 1}
            for imageName, glassesExpectedResult in cases.items():
                with self.subTest(image=imageName.split("/")[-1]):
                    reply_info = luna_api_functions.extractDescriptors(headers, filename=imageName,
                                                                       estimateAttributes=True,
                                                                       estimateEthnicities=True)
                    self.assertEqual(reply_info.body['faces'][0]['attributes']['eyeglasses'], glassesExpectedResult,
                                     reply_info.body['faces'][0]['attributes'])

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_quality(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_quality

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate quality
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (0, 1)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                                      estimateQuality=True,
                                                                      extractDescriptor=extractDescriptor, )
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertIn('light', replyInfo.body['faces'][0]['quality'], authStr(auth))
                    self.assertIn('saturation', replyInfo.body['faces'][0]['quality'], authStr(auth))
                    self.assertIn('dark', replyInfo.body['faces'][0]['quality'], authStr(auth))
                    self.assertIn('blurriness', replyInfo.body['faces'][0]['quality'], authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_score_threshold(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_quality

            :resources: "/storage/descriptors"
            :description: success extract descriptors with score threshold
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            threshold = 0.9
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=severalFaces, scoreThreshold=threshold)
            self.assertSuccessExtractPhoto(replyInfo, authStr(auth))
            self.assertTrue(1 < len(replyInfo.body['faces']) < 9)
            for face in replyInfo.body['faces']:
                self.assertGreaterEqual(face['score'], threshold, authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_quality_is_low(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_quality

            :resources: "/storage/descriptors"
            :description: success extract descriptors with score threshold
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest_quality_is_low(headers, auth):
            threshold = 1
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage, scoreThreshold=threshold)
            self.assertEqual(replyInfo.statusCode, 400)
            self.assertEqual(replyInfo.body["detail"],
                             Error.LowThreshold.description + ". Detail: No faces found.", auth)
            self.assertEqual(replyInfo.body["error_code"],
                             Error.LowThreshold.errorCode, auth)

        extractPhotoTest_quality_is_low()

    def test_descriptor_not_extract_descriptor_with_score_threshold(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_quality

            :resources: "/storage/descriptors"
            :description: success
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            threshold = 1
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=severalFaces, scoreThreshold=threshold,
                                                              extractDescriptor=False)
            self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
            self.assertTrue(len(replyInfo.body['faces']) == 9, authStr(auth))
            for face in replyInfo.body['faces']:
                self.assertNotIn('score', face, authStr(auth))

        extractPhotoTest()

    def test_descriptor_not_extract_descriptor(self):
        """
        .. test:: test_descriptor_not_extract_descriptor

            :resources: "/storage/descriptors"
            :description: does not extract descriptor
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage, extractDescriptor=False)
            self.assertTrue(replyInfo.statusCode == 201, authStr(auth))
            self.assertNotIn('id', replyInfo.body['faces'][0], authStr(auth))

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_exif(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_exif

            :resources: "/storage/descriptors"
            :description: success extract descriptor with exif
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (0, 1)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=exifWarpedImage,
                                                                      extractExif=True,
                                                                      extractDescriptor=extractDescriptor)
                    self.assertIn('exif', replyInfo.body, authStr(auth))
                    self.assertIn('model', replyInfo.body['exif'], authStr(auth))
                    self.assertIn('make', replyInfo.body['exif'], authStr(auth))
                    self.assertIn('artist', replyInfo.body['exif'], authStr(auth))

        extractPhotoTest()

    def test_descriptor_not_extract_descriptor_with_angle_threshold(self):
        """
        .. test:: test_descriptor_not_extract_descriptor_with_angle_threshold

            :resources: "/storage/descriptors"
            :description: success
            :LIS: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            thresholds = [{"name": "pitchLt", "value": 10}, {"name": "yawLt", "value": 12},
                          {"name": "rollLt", "value": 10}]
            for threshold in thresholds:
                with self.subTest(threshold=threshold["name"]):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=severalFaces,
                                                                      **{threshold["name"]: threshold["value"]})
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertTrue(1 < len(replyInfo.body['faces']) < 9)
                    self.assertIn('head_pose', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    for angle in ("yaw", "pitch", "roll"):
                        self.assertIn(angle, replyInfo.body['faces'][0]['attributes']['head_pose'])

        extractPhotoTest()

    def test_descriptor_extract_descriptor_with_head_angles(self):
        """
        .. test:: test_descriptor_extract_descriptor_with_head_angles

            :resources: "/storage/descriptors"
            :description: success extract descriptor with estimate head angles
            :S3: No
            :tag: Descriptor
        """

        @self.authorization
        def extractPhotoTest(headers, auth):
            extractDescriptors = (0, 1)
            for extractDescriptor in extractDescriptors:
                with self.subTest(extractDescriptor=extractDescriptor):
                    replyInfo = luna_api_functions.extractDescriptors(headers, filename=standardImage,
                                                                      estimateAttributes=True,
                                                                      estimateHeadPose=True)
                    self.assertSuccessStorageDescriptor(replyInfo, authStr(auth))
                    self.assertIn('head_pose', replyInfo.body['faces'][0]['attributes'], authStr(auth))
                    for angle in ("yaw", "pitch", "roll"):
                        self.assertIn(angle, replyInfo.body['faces'][0]['attributes']['head_pose'])

        extractPhotoTest()
