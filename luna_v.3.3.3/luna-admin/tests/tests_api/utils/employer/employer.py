from lunavl import httpclient
from utils.common.config_loader import ConfigLoader
from utils.common.data_generator import DataGenerator


class Employer:

    def __init__(self, email = DataGenerator.generate_email(), password = "password", org_name = "TestOrg"):
        self.email = email
        self.password = password
        self.org_name = org_name
        self.token = None

        endPoint = ConfigLoader.get_api_url().split(":")[0] + ":" + ConfigLoader.get_api_url().split(":")[1]
        port = ConfigLoader.get_api_url().split(":")[-1].split("/")[0]
        api = ConfigLoader.get_api_url().split(":")[-1].split("/")[1]
        self.api_client = httpclient.LunaHttpClient(login = email, password = password, endPoint = endPoint,
                                                    port = port, api = int(api))
