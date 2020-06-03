from configs.config import STORAGE_TYPE
from crutches_on_wheels.handlers.base_handler_class import VLBaseHandler
from storage.aerospike_cache import AerospikeCache
from storage.aws_s3.s3_driver import S3Driver
from storage.local_storage.disk_driver import DiskDriver
from storage.store_interface import StoreInterface


class BaseRequestHandler(VLBaseHandler):
    """
    Base handler for other handlers.
    """

    def initialize(self) -> None:
        """
        Initialize logger for request and create request id and contexts to storage and cache.
        """
        super().initialize()

        self.storageCtx = self.createStorageContext()
        self.storageCache = AerospikeCache(self.logger)

    def createStorageContext(self)-> StoreInterface:
        """
        Create Context.

        Returns:
            DiskDriver if STORAGE_TYPE is equal to "LOCAL", S3Driver is equal to S3
        Raises:
            ValueError - if incorrect STORAGE_TYPE
        """
        if STORAGE_TYPE == "LOCAL":
            return DiskDriver(self.logger)
        elif STORAGE_TYPE == "S3":
            return S3Driver(self.logger)
        raise ValueError
