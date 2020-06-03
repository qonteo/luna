from base_class import BaseClass
from datetime import datetime
from dateutil import parser
import time
import pytz
from tzlocal import get_localzone

from resources.resources import warp, no_faces, several_faces
from utils.common.switch import switch

utc = pytz.timezone(get_localzone().zone)


def get_time(time_str):
    date_time = parser.parse(time_str)
    return date_time


def get_iso_format(t):
    return t.isoformat("T")


class TestStatistic(BaseClass):
    start = None
    end = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.start = datetime.now(get_localzone()).replace(microsecond=0)

        time.sleep(2)
        person_id = TestStatistic.employer.api_client.createPerson(raiseError=True).body["person_id"]
        descriptor_id = TestStatistic.employer.api_client.extractDescriptors(
            filename=warp,
            warpedImage=True, raiseError=True).body["faces"][0]["id"]
        TestStatistic.employer.api_client.extractDescriptors(
            filename=no_faces)
        TestStatistic.employer.api_client.linkDescriptorToPerson(person_id, descriptor_id, raiseError=True)
        TestStatistic.employer.api_client.identify(personId=person_id, personIds=[person_id], raiseError=True)
        TestStatistic.employer.api_client.match(personId=person_id, descriptorIds=[descriptor_id],
                                                raiseError=True)
        TestStatistic.employer.api_client.verify(personId=person_id, descriptorId=descriptor_id, raiseError=True)
        TestStatistic.employer.api_client.search(descriptorIds=[descriptor_id],
                                                 filename=warp,
                                                 raiseError=True)
        TestStatistic.employer.api_client.search(descriptorIds=[descriptor_id],
                                                 filename=several_faces,
                                                 raiseError=False)
        TestStatistic.employer.api_client.search(descriptorIds=[descriptor_id],
                                                 filename=no_faces,
                                                 raiseError=False)
        cls.end = datetime.now(get_localzone()).replace(microsecond=0)
        time.sleep(1)
        TestStatistic.employer.api_client.match(personId=person_id, descriptorIds=[descriptor_id],
                                                raiseError=True)

    def test_statistic_by_period(self):
        for resource in ["extract_success", "matching_success", "errors"]:
            with self.subTest(resource=resource):
                response = TestStatistic.admin_client.get_statistic(resource, {"group_by": "1s",
                                                                               "time__lt": get_iso_format(
                                                                                   TestStatistic.end),
                                                                               "time__gte": get_iso_format(
                                                                                   TestStatistic.start),
                                                                               })
                self.assertEqual(200, response.status_code)
                response_start_period = get_time(response.content["values"][0][0])
                self.assertTrue(response_start_period >= TestStatistic.start,
                                "{}, {}".format(response_start_period, TestStatistic.start))
                response_end_period = get_time(response.content["values"][-1][0])
                self.assertTrue(response_end_period <= TestStatistic.end)

    def test_statistic_group_time(self):

        for resource in ["extract_success", "matching_success", "errors"]:
            with self.subTest(resource=resource):
                for group_step in ["s", "d", "w", "h", "m"]:
                    with self.subTest(group_step=group_step):
                        response = TestStatistic.admin_client.get_statistic(resource,
                                                                            {"group_by": "1{}".format(group_step)
                                                                             })
                        self.assertEqual(200, response.status_code)
                        response_start_period = get_time(response.content["values"][0][0])
                        for case in switch(group_step):
                            if case("w"):
                                self.assertEqual(0, response_start_period.hour)
                            if case("d"):
                                self.assertEqual(0, response_start_period.hour)
                            if case("h"):
                                self.assertEqual(0, response_start_period.minute)
                            if case("m"):
                                self.assertEqual(0, response_start_period.second)
                            if case("s"):
                                self.assertEqual(0, response_start_period.microsecond)
                            if case():
                                continue

    def test_statistic_by_account(self):

        for resource in ["extract_success", "matching_success", "errors"]:
            with self.subTest(resource=resource):
                accounts = [{"account_id": TestStatistic.employer.account_id, "count": 1},
                            {"account_id": TestStatistic.employer2.account_id, "count": 0}]
                for account in accounts:
                    response = TestStatistic.admin_client.get_statistic(resource,
                                                                        {
                                                                            "account_id": account["account_id"]})
                    self.assertEqual(200, response.status_code)
                    if account["count"]:
                        self.assertTrue(len(response.content["values"]) > 0)
                    else:
                        self.assertDictEqual({}, response.content)

    def test_statistic_by_matcing_resource(self):
        for resource in ["search", "match", "identify", "verify"]:
            with self.subTest(resource=resource):
                response = TestStatistic.admin_client.get_statistic("matching_success",
                                                                    {
                                                                        "account_id": TestStatistic.employer.account_id,
                                                                        "resource": resource,
                                                                        "group_by": "1ms"
                                                                    })
                self.assertEqual(200, response.status_code)
                self.assertTrue(len(response.content["values"]), 1)
        response = TestStatistic.admin_client.get_statistic("matching_success",
                                                            {
                                                                "account_id": TestStatistic.employer.account_id,
                                                                "group_by": "1ms"
                                                            })
        self.assertEqual(200, response.status_code)
        self.assertTrue(len(response.content["values"]), 4)

    def test_statistic_agregators(self):
        def test_count():
            for resource in ["extract_success", "matching_success"]:
                with self.subTest(resource=resource):
                    response = TestStatistic.admin_client.get_statistic(resource, {"aggregator": "count",
                                                                                   "account_id": TestStatistic.employer.account_id})
                    self.assertEqual(200, response.status_code)
                    for value in response.content["values"]:
                        for v in value[1:]:
                            self.assertEqual(type(v), int)
                    for column in response.content["columns"][1:]:
                        self.assertTrue(column.startswith("count"))

        def test_max_min_mean():
            agregators = [{"agregator": "max", "res": {}}, {"agregator": "min", "res": {}},
                          {"agregator": "mean", "res": {}}]
            for agregator in agregators:
                response = TestStatistic.admin_client.get_statistic("matching_success",
                                                                    {"aggregator": agregator["agregator"],
                                                                     "account_id": TestStatistic.employer.account_id})
                agregator["res"] = response.content["values"]
                for column in response.content["columns"][1:]:
                    self.assertTrue(column.startswith(agregator["agregator"]))

            for i in range(len(agregators[0]["res"])):
                for j in range(len(agregators[0]["res"][1:])):
                    self.assertTrue(agregators[0]["res"][i][j] > agregators[2]["res"][i][j])
                    self.assertTrue(agregators[2]["res"][i][j] > agregators[1]["res"][i][j])

        test_count()
        test_max_min_mean()

    def test_other_params(self):
        params = [
            {"name": "server", "value": "127.0.0.1", "resources": ["extract_success", "matching_success", "errors"]},
            {"name": "limit", "value": 4, "resources": ["matching_success"]},
            {"name": "template", "value": 1, "resources": ["matching_success"]},
            {"name": "candidate", "value": 1, "resources": ["matching_success"]},
            {"name": "count_faces", "value": 3, "resources": ["matching_success"]}]
        for param in params:
            with self.subTest(param=param["name"]):
                for resource in param["resources"]:
                    with self.subTest(resource=resource):
                        response = TestStatistic.admin_client.get_statistic(resource, {param["name"]: param["value"]})
                        self.assertEqual(200, response.status_code)

    def test_bad_params(self):
        bad_params = [
            {"name": "aggregator", "value": "c", "resources": ["extract_success", "matching_success", "errors"]},
            {"name": "group_by", "value": "3sec", "resources": ["extract_success", "matching_success", "errors"]}]
        for bad_param in bad_params:
            with self.subTest(param_name=bad_param["name"]):
                for resource in bad_param["resources"]:
                    with self.subTest(resource=resource):
                        self.badParamTests({bad_param["name"]: bad_param["value"]},
                                           BaseClass.admin_client.get_statistic,
                                           resource=resource)

    def test_error_code(self):
        errors = [{"errror_code": 4003, "count": 2}, {"errror_code": 11012, "count": 1}]
        for error in errors:
            with self.subTest(errror_code=error["errror_code"]):
                response = TestStatistic.admin_client.get_statistic("errors", {"aggregator": "count",
                                                                               "account_id": TestStatistic.employer.account_id,
                                                                               "error": error["errror_code"],
                                                                               "group_by": "1d"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content["values"][0][1], error["count"])

    def test_error_resource(self):
        errors = [{"resource": "descriptors", "count": 1}, {"resource": "search", "count": 2}]
        for error in errors:
            with self.subTest(resource=error["resource"]):
                response = TestStatistic.admin_client.get_statistic("errors", {"aggregator": "count",
                                                                               "account_id": TestStatistic.employer.account_id,
                                                                               "resource": error["resource"],
                                                                               "group_by": "1d"})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content["values"][0][1], error["count"])

    def test_method_not_allowed(self):
        for resource in ["extract_success", "matching_success", "errors"]:
            with self.subTest(resource=resource):
                self.methodNotAllowed("{}/realtime_statistics/{}".format(TestStatistic.admin_client.url, resource),
                                      ["post", "put", "delete", "patch"])
