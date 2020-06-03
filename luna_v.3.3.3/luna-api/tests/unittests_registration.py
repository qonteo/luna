# -*- coding: utf-8 -*-
import unittest

from faker import Factory

from crutches_on_wheels.errors.errors import Error
from tests.functions import checkUUID4
from tests import luna_api_functions

fake = Factory.create()


class TestRegistration(unittest.TestCase):
    """
    Tests of registration
    """
    def test_registration_ok(self):
        """

        .. test:: test_registration_ok

            :resources: "/accounts"
            :description: success registration, every time random email
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "organization_name": "Horns and hooves",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 201)
        self.assertTrue("token" in reply.body)
        self.assertTrue(checkUUID4(reply.body["token"]))


    def test_registration_upper_case(self):
        """

        .. test:: test_registration_upper_case

            :resources: "/accounts"
            :description: success registration with upper letters, every time random email
            :LIS: No
            :tag: Registration
        """
        email = fake.email().upper()
        payload = {"email": email,
                   "organization_name": "Horns and hooves",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 201)
        self.assertTrue("token" in reply.body)
        self.assertTrue(checkUUID4(reply.body["token"]))

        for emailForAuth in [email,  email.lower()]:

            replyInfo = luna_api_functions.getAccountData(emailForAuth, "secretpassword")
            self.assertEqual(replyInfo.statusCode, 200)
            self.assertTrue("email" in replyInfo.body)
            self.assertEqual(email.lower(), replyInfo.body["email"])
            self.assertTrue("suspended" in replyInfo.body)
            self.assertEqual(False, replyInfo.body["suspended"])
            self.assertTrue("organization_name" in replyInfo.body)
            self.assertEqual("Horns and hooves", replyInfo.body["organization_name"])

    def test_registration_bad_email(self):
        """
        .. test:: test_registration_bad_email

            :resources: "/accounts"
            :description: non correct email field in json, hornsandhooves155432\@ya,ru
            :LIS: No
            :tag: Registration
        """
        payload = {"email": "hornsandhooves155432@ya,ru",
                   "organization_name": "Horns and hooves",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.IncorrectEmail.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.IncorrectEmail.detail)

    def test_registration_without_email(self):
        """
        .. test:: test_registration_without_email

            :resources: "/accounts"
            :description: registration json without email
            :LIS: No
            :tag: Registration
        """
        payload = {"organization_name": "Horns and hooves",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.FieldNotInJSON.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.FieldNotInJSON.detail.format("email"))

    def test_registration_without_password(self):
        """
        .. test:: test_registration_without_password

            :resources: "/accounts"
            :description: registration json without password
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "organization_name": "Horns and hooves"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.FieldNotInJSON.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.FieldNotInJSON.detail.format("password"))

    def test_registration_without_org_name(self):
        """
        .. test:: test_registration_without_org_name

            :resources: "/accounts"
            :description: registration json without organization_name
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.FieldNotInJSON.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.FieldNotInJSON.detail.format("organization_name"))

    def test_registration_empty_email(self):
        """
        .. test:: test_registration_empty_email

            :resources: "/accounts"
            :description: registration json with empty email
            :LIS: No
            :tag: Registration
        """
        payload = {"email": "",
                   "organization_name": "Horns and hooves",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.EmptyField.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.EmptyField.detail.format("email"))

    def test_registration_empty_password(self):
        """
        .. test:: test_registration_password

            :resources: "/accounts"
            :description: registration json with empty password
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "password": "",
                   "organization_name": "Horns and hooves"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.EmptyField.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.EmptyField.detail.format("password"))

    def test_registration_empty_org_name(self):
        """
        .. test:: test_registration_empty_org_name

            :resources: "/accounts"
            :description: registration json with empty organization_name
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "organization_name": "",
                   "password": "secretpassword"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.EmptyField.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.EmptyField.detail.format("organization_name"))

    def test_registration_short_password(self):
        """
        .. test:: test_registration_short_password

            :resources: "/accounts"
            :description: password is very short, length  8
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "password": "1",
                   "organization_name": "Horns and hooves"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.PasswordBadLength.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.PasswordBadLength.detail)

    def test_registration_long_password(self):
        """
        .. test:: test_registration_short_password

            :resources: "/accounts"
            :description: password is very long, length is more 32
            :LIS: No
            :tag: Registration
        """
        payload = {"email": fake.email(),
                   "password": "123456789012345678901234567890123",
                   "organization_name": "Horns and hooves"}
        reply = luna_api_functions.registration(payload)
        self.assertEqual(reply.statusCode, 400)
        self.assertTrue("error_code" in reply.body)
        self.assertEqual(reply.body["error_code"], Error.PasswordBadLength.errorCode)
        self.assertTrue("detail" in reply.body)
        self.assertEqual(reply.body["detail"], Error.PasswordBadLength.detail)
