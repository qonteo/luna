# -*- coding: utf-8 -*-
"""Version module

Tests of common errors: "page not found",  "method not allowed" and others.
"""
from luna_index_manager.crutches_on_wheels.errors.errors import Error
from tests.config import SERVER_ORIGIN, SERVER_API_VERSION
from tests.base_test_class import TestBase
import requests


class CommonErrorsTest(TestBase):
    """
    Tests common  errors: "page not found",  "method not allowed" and others.
    """

    def test_404_page(self):
        """
        Test for not exist resource.

        .. test::test_404_page

            :description: Getting non exist resource.
            :resources: '/1/version'
        """
        response = requests.get("{}/{}/version".format(SERVER_ORIGIN, SERVER_API_VERSION))
        self.assertApiError(response.status_code, response.json(), 404, Error.PageNotFoundError)

    def test_405_method_not_allowed(self):
        """

        .. test::test_405_method_not_allowed

            :description: do request to resources with  not allowed methods.
            :resources: '/version'

        """
        class Resource:
            def __init__(self, resourceName, allowedMethods):
                if resourceName != "version":
                    self.resource = "{}/{}".format(SERVER_ORIGIN, SERVER_API_VERSION, resourceName)
                else:
                    self.resource = "{}/{}".format(SERVER_ORIGIN, resourceName)
                self.allowedMethods = allowedMethods

        testingResources = (Resource("version", ("GET",)),)
        allMethods = ("POST", "PUT", "PATCH", "DELETE", "PATCH", "GET", "OPTIONS")
        for resource in testingResources:
            for method in allMethods:
                with self.subTest(resource=resource.resource, method=method):
                    if method in resource.allowedMethods:
                        continue
                    if method == 'POST':
                        response = requests.post(resource.resource)
                    elif method == 'PUT':
                        response = requests.put(resource.resource)
                    elif method == 'PATCH':
                        response = requests.patch(resource.resource)
                    elif method == 'DELETE':
                        response = requests.delete(resource.resource)
                    elif method == 'GET':
                        response = requests.get(resource.resource)
                    elif method == 'OPTIONS':
                        response = requests.options(resource.resource)

                    self.assertApiError(response.status_code, response.json(), 405, Error.MethodNotAllowed)
