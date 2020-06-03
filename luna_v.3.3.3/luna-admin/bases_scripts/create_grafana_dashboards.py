import os
import requests
import base64
import ujson as json
from string import Template

import sys

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "luna_admin")))

from configs.config import ADMIN_STATISTICS_DB, ADMIN_STATISTICS_SERVER_ORIGIN, GRAFANA_ORIGIN


def generatePathToDashboards(current_dir):
    dashboards = [("{}/grafana_dashboards/errors_dashboard.json.in".format(current_dir), "Errors"),
                  ("{}/grafana_dashboards/extract_dashboard.json.in".format(current_dir), "Extract"),
                  ("{}/grafana_dashboards/matching_dashboard.json.in".format(current_dir), "Match"),
                  ("{}/grafana_dashboards/gc_dashboard.json.in".format(current_dir), "GC")]
    return dashboards


def createBasicAuthHeader(login, password):
    strAuth = login + ":" + password
    base64Auth = base64.b64encode(str.encode(strAuth)).decode("utf-8")
    headers = {'Authorization': 'Basic ' + base64Auth}
    return headers


def createDataSource():
    source = {
        "name": ADMIN_STATISTICS_DB,
        "type": "influxdb",
        "url": ADMIN_STATISTICS_SERVER_ORIGIN,
        "access": "proxy",
        "basicAuth": False,
        "database": ADMIN_STATISTICS_DB
    }
    headers = createBasicAuthHeader("admin", "admin")
    headers["Content-Type"] = "application/json"
    reply = requests.post(url=GRAFANA_ORIGIN + "/api/datasources", headers=headers,
                          data=json.dumps(source))
    print(reply.text)
    print(reply.status_code)


def createDashboard(dashboardFilePath, dashboardName, dbSource):
    dashboardFile = open(dashboardFilePath)
    dachboardTemplateStr = Template(dashboardFile.read())
    dashboardStr = dachboardTemplateStr.substitute({"dashboard_name": dashboardName, "datasource": dbSource})
    jsonDashboard = json.loads(dashboardStr)

    headers = createBasicAuthHeader("admin", "admin")
    headers["Content-Type"] = "application/json"
    reply = requests.post(url=GRAFANA_ORIGIN + "/api/dashboards/db", headers=headers, data=json.dumps(jsonDashboard))

    print(reply.text)
    print(reply.status_code)


if __name__ == "__main__":
    createDataSource()

    dashboards = generatePathToDashboards(basedir)
    for dashboard in dashboards:
        createDashboard(dashboard[0], dashboard[1], ADMIN_STATISTICS_DB)
