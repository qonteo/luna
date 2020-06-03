import base64

import requests

from utils.common.config_loader import ConfigLoader
from utils.luna_admin_utils.response import Response


def createBasicAuthHeader(login, password):
    strAuth = login + ":" + password
    base64Auth = base64.b64encode(str.encode(strAuth)).decode("utf-8")
    headers = {'Authorization': 'Basic ' + base64Auth}
    return headers


class LunaAdminUtils:

    def __init__(self):
        self.auth_header = createBasicAuthHeader("root", "root")
        self.url = ConfigLoader.get_admin_url()

    def get_grafana(self):
        return Response.fromHttpResponse(requests.get(url = self.url + "/grafana", headers = self.auth_header))

    def get_config(self):
        return Response.fromHttpResponse(requests.get(url = self.url + "/config", headers = self.auth_header))

    def get_persons(self, params = None):
        return Response.fromHttpResponse(requests.get(url = self.url + "/persons", headers = self.auth_header,
                                                      params = params))

    def unblock_persons(self, params = None):
        return Response.fromHttpResponse(requests.patch(url = self.url + "/persons", headers = self.auth_header,
                                                        params = params))

    def unblock_lists(self, params = None):
        return Response.fromHttpResponse(requests.patch(url = self.url + "/lists", headers = self.auth_header,
                                                        params = params))

    def get_lists(self, params = None):
        return Response.fromHttpResponse(requests.get(url = self.url + "/lists", headers = self.auth_header,
                                                      params = params))

    def get_list(self, list_id):
        return Response.fromHttpResponse(requests.get(url = self.url + "/lists/" + list_id,
                                                      headers = self.auth_header))

    def get_luna_lists(self, list_id, params = None):
        return Response.fromHttpResponse(requests.get(url = "{}/lists/{}/luna_lists".format(self.url, list_id),
                                                      headers = self.auth_header, params = params))

    def get_person(self, person_id):
        return Response.fromHttpResponse(requests.get(url = self.url + "/persons/" + person_id,
                                                      headers = self.auth_header))

    def search(self, params):
        return Response.fromHttpResponse(requests.get(url = self.url + "/search", headers = self.auth_header,
                                                      params = params))

    def get_accounts(self, params = None):
        return Response.fromHttpResponse(requests.get(url = self.url + "/accounts", headers = self.auth_header,
                                                      params = params))

    def get_account(self, account_id):
        return Response.fromHttpResponse(requests.get(url = self.url + "/accounts/" + account_id,
                                                      headers = self.auth_header))

    def patch_account(self, account_id, status):
        return Response.fromHttpResponse(requests.patch(url = self.url + "/accounts/" + account_id,
                                                        headers = self.auth_header, params = {"status": status}))

    def get_account_tokens(self, account_id):
        return Response.fromHttpResponse(requests.get(url = "{}/accounts/{}/tokens".format(self.url, account_id),
                                                      headers = self.auth_header))

    def get_statistic(self, resource, params = None):
        return Response.fromHttpResponse(requests.get(url = "{}/realtime_statistics/{}".format(self.url, resource),
                                                      params = params,
                                                      headers = self.auth_header))

    def start_gc(self, params):
        return Response.fromHttpResponse(requests.post(url = "{}/gc".format(self.url),
                                                       params = params,
                                                       headers = self.auth_header))

    def get_task(self, task_id):
        return Response.fromHttpResponse(requests.get(url = "{}/tasks/{}".format(self.url, task_id),
                                                      headers = self.auth_header))

    def stop_task(self, task_id):
        return Response.fromHttpResponse(requests.delete(url = "{}/tasks/{}".format(self.url, task_id),
                                                         headers = self.auth_header))

    def start_reextract_descriptors(self, descriptors = None):
        if descriptors is not None:
            return Response.fromHttpResponse(requests.post(url = "{}/reextract".format(self.url),
                                                           json = descriptors,
                                                           headers = self.auth_header))
        else:
            return Response.fromHttpResponse(requests.post(url = "{}/reextract".format(self.url),
                                                           headers = self.auth_header))

    def get_task_errors(self, task_id, params = None):
        return Response.fromHttpResponse(requests.get(url = "{}/tasks/{}/errors".format(self.url, task_id),
                                                      headers = self.auth_header, params = params))
