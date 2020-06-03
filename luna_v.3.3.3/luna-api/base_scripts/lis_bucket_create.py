from set_working_directory import setWorkingDirectory

setWorkingDirectory()

from luna3.client import Client
from configs.config import LUNA_IMAGE_STORE_API_VERSION, LUNA_IMAGE_STORE_ORIGIN, LUNA_IMAGE_STORE_BUCKET

luna3Client = Client()

luna3Client.updateLunaImageStoreSettings(origin=LUNA_IMAGE_STORE_ORIGIN, api=LUNA_IMAGE_STORE_API_VERSION,
                                         asyncRequest=False)

luna3Client.lunaImageStore.createBucket(LUNA_IMAGE_STORE_BUCKET, raiseError=True)
