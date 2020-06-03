import requests

from utils.common.config_loader import ConfigLoader


class LunaCoreUtils:

    def __init__(self):
        self.url = ConfigLoader.get_luna_core_url()

    def get_descriptor(self, desc_id):
        resp = requests.get(
            url=self.url+"/descriptors?id={0}".format(desc_id),
            headers={
                "Accept": "application/x-vl-xpk"
            }
        )
        return resp

    def delete_descriptor(self, desc_id):
        return requests.delete(url=self.url + "/descriptors?id={0}".format(desc_id),
                               headers={"Content-Type": "application/json"}
                               )

    def put_list(self, list_id, descriptors_list):
        return requests.put(url=self.url + "/lists",
                            params={"id": list_id},
                            json={"data": descriptors_list})

    def get_list(self, list_id):
        return requests.get(url=self.url + "/lists",
                            params={"id": list_id})