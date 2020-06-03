import unittest
import ujson as json
import datetime
import requests
import jsonschema
import dateutil.parser
from resources.resources import warp
from schemas import ERROR_SCHEMA
from utils.common.config_loader import ConfigLoader
from utils.common.data_generator import DataGenerator
from utils.db.sql_utils import SqlUtils
from utils.employer.employer import Employer
from utils.luna_admin_utils.luna_admin_utils import LunaAdminUtils


def createEmployer(email, password, org_name):
    admin_client = LunaAdminUtils()
    employer = Employer(email, password, org_name)
    requests.post(
        url="{}/{}".format(ConfigLoader.get_api_url(),
                           "accounts"),

        data=json.dumps(
            {
                "organization_name": org_name,
                "email": email,
                "password": password
            }
        )
    )
    employer.account_id = admin_client.search({"q": email}).content["data"]["info"]["account_id"]
    return employer


class BaseClass(unittest.TestCase):
    employer = None
    employer2 = None
    admin_client = LunaAdminUtils()
    sqlUtils = SqlUtils()

    @classmethod
    def setUpClass(cls):
        if cls.employer is None:
            org_name = "TestOrg"
            email = "admintest" + DataGenerator.generate_email()
            email_ = "admintest" + DataGenerator.generate_email()
            password = "password"
            cls.employer = createEmployer(email, password, org_name)
            cls.employer2 = createEmployer(email_, password, org_name)

    def assertSchema(self, input, schema):
        jsonschema.validate(input, schema)

    def badParamTests(self, params, request_function, **kwargs):
        for param_name, value in params.items():
            with self.subTest(param_name=param_name):
                response = request_function(params={param_name: value}, **kwargs)
                self.assertEqual(response.status_code, 400)
                self.assertBadParam(response.content, param_name)

    def methodNotAllowed(self, resource, methods):
        for method in methods:
            with self.subTest(method=method):
                response = requests.__dict__[method](resource, headers=BaseClass.admin_client.auth_header)
                self.assertSchema(response.json(), ERROR_SCHEMA)
                self.assertEqual(405, response.status_code)
                self.assertEqual(12021, response.json()["error_code"])

    def assertBadParam(self, input_json, name):
        self.assertSchema(input_json, ERROR_SCHEMA)
        self.assertEqual(input_json["error_code"], 12012)
        self.assertEqual(input_json["detail"], "Bad query parameters '{}'".format(name))

    def assertTaskInfo(self, task_info, task_id, target, error_count):
        self.assertEqual(task_info["progress"], 1, str(task_info))
        self.assertEqual(task_info["target"], target)
        self.assertEqual(task_info["status"], True)
        self.assertEqual(task_info["task_id"], task_id)
        self.assertEqual(task_info["error_count"], error_count)
        duration = datetime.datetime.strptime(task_info["duration"], '%H:%M:%S').time()
        self.assertTrue(duration < datetime.time(0, 0, 5))
        self.assertTrue((datetime.datetime.now() - dateutil.parser.parse(task_info["start_time"]).replace(
            tzinfo=None)).total_seconds() < 5)

    def assertErrorRestAnswer(self, reply, statusCode, error, msgFormat=None):
        self.assertEqual(reply.status_code, statusCode)
        reply.json = reply.content
        self.assertEqual(reply.json['desc'], error.description)
        if msgFormat is None:
            self.assertEqual(reply.json['detail'], error.detail)
        else:
            self.assertEqual(reply.json['detail'], error.detail.format(*msgFormat))
        self.assertEqual(reply.json['error_code'], error.errorCode)

    @staticmethod
    def createDescriptor(employer):
        return employer.api_client.extractDescriptors(filename=warp, warpedImage=True,
                                                      raiseError=True).body["faces"][0]["id"]
