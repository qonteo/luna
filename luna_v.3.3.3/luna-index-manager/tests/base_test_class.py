import unittest
from jsonschema import validate
from luna_index_manager.crutches_on_wheels.errors.errors import ErrorInfo
from typing import Union

from tests.schemas import ERROR_SCHEMA


class TestBase(unittest.TestCase):

    @staticmethod
    def validateJson(data: Union[list, dict, int], schema: dict) -> None:
        """
        Validate json.

        Args:
            data: json for validation
            schema: json schema

        Raises:
            VLException(Error.BadInputJson, 400): if failed  to validate schema
        """
        validate(data, schema)

    def assertApiError(self, statusCode: int, errorJson: dict, expectedStatusCode: int, expectedError: ErrorInfo):
        """
        Assert API Error.

        Args:
            statusCode: received status code in response
            errorJson: received json in response
            expectedStatusCode: expected status code
            expectedError: expected error
        """

        self.assertEqual(statusCode, expectedStatusCode)
        self.validateJson(errorJson, ERROR_SCHEMA)
        self.assertEqual(errorJson["desc"], expectedError.description)
        self.assertEqual(errorJson["error_code"], expectedError.errorCode)
