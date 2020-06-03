from functools import wraps
from typing import Union, Callable, List, Tuple, Dict

from configs import config
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException

if config.CACHE_ENABLED:
    import aerospike


class AerospikeAPI:
    """
    API for work with aerospike DB

    Attributes:
        hosts: list of (address, port, [tls-name]) tuples identifying a node (or multiple nodes) in the cluster.
        username: username for auth in aerospike
        password: password for auth in aerospike
        namespace: default namespace
        set_: default set
        config: client’s configuration exclude hosts.
                        config details - https://www.aerospike.com/apidocs/python/aerospike.html#aerospike.client
        _client: store established connection
    """
    def __init__(self, hosts: List[Tuple[Union[str, int]]] = (('127.0.0.1', 3000),),
                 username: str = None, password: str = None,
                 namespace: str = None, set_: str = None, config: dict = None) -> None:

        self.hosts = hosts
        self.username = username
        self.password = password
        self.defaultNamespace = namespace
        self.defaultSet = set_

        if not config:
            config = {}
        config.update({'hosts': self.hosts})
        self._client = aerospike.client(config).connect(self.username, self.password)

    def getNamespace(self, namespace: str) -> str:
        """
        Return final namespace

        Args:
            namespace: aerospike namespace
            aerospike namespace
        """
        return namespace if namespace else self.defaultNamespace

    def getSet(self, set_: str) -> str:
        """
        Return final set

        Args:
            set_: aerospike set

        Returns:
            aerospike set
        """
        return set_ if set_ else self.defaultSet

    def get(self, key: str, set_: str=None, namespace: str=None, simple: bool=True) -> Union[dict, tuple, None]:
        """
        Get data from db

        Args:
            key: aerospike bins
            set_: set
            namespace: namespace
            simple: if true return only data else return tuple (key, meta, bins)

        Returns:
            tuple (key, meta, bins) or bins or None if no data. Depending on simple mode.
        """
        try:
            response = self._client.get((self.getNamespace(namespace), self.getSet(set_), key))
        except aerospike.exception.RecordNotFound:
            return None
        else:
            if simple:
                return response[2]
            else:
                return response

    def info_all(self, command: str) -> Dict[str, tuple]:
        """
        Send an info command to all nodes in the cluster to which the client is connected

        Args:
            command: the info command

        Returns:
            structure with response
        """
        return self._client.info_all(command)

    def put(self, key: str, data, set_: str=None, namespace: str=None, meta: dict=None) -> None:
        """
        Put data by key

        Args:
            key: store key
            data: data to be saved
            set_: set for store
            namespace: namespace for store
            meta: meta config
        """
        key = (self.getNamespace(namespace), self.getSet(set_), key)
        self._client.put(key, data, meta=meta)

    def remove(self, key: str, set_: str=None, namespace: str=None) -> bool:
        """
        Remove data by key from db.

        Args:
            key: key for remove
            set_: set where it will be searched
            namespace: namespace where it will be searched

        Returns:
            True if removed or False if key not be found
        """
        try:
            self._client.remove((self.getNamespace(namespace), self.getSet(set_), key))
        except aerospike.exception.RecordNotFound:
            return False
        else:
            return True


def aerospikeExceptionWrap(func: Callable) -> Callable:
    """
    Decorator for catching aerospike exceptions.

    Args:
        func: decorated function

    Returns:
        if exception was caught, system calls error method with error
    """
    @wraps(func)
    def wrap(*func_args, **func_kwargs):
        try:
            return func(*func_args, **func_kwargs)
        except aerospike.exception.ServerError as e:
            func_args[0].logger.exception()
            raise VLException(Error.AerospikeServerError, exception=e)
        except aerospike.exception.ClientError as e:
            func_args[0].logger.exception()
            raise VLException(Error.AerospikeClientError, exception=e)
        except Exception as e:
            func_args[0].logger.exception()
            raise VLException(Error.AerospikeUnknownError, exception=e)
    return wrap


class AerospikeCache:
    """
    High-level api for caching images in aerospike db.

    Attributes:
        logger: logger instance for logging errors
        args: args for configure low-level AerospikeAPI
        kwargs: kwargs for configure low-level AerospikeAPI
    """
    @classmethod
    def initModule(cls, *args, **kwargs):
        """
        initialize cache lib.

        Args:
            *args: AerospikeAPI args
            **kwargs: AerospikeAPI kwargs
        """
        cls.api = AerospikeAPI(*args, **kwargs)

    def __init__(self, logger):
        self.logger = logger

    @aerospikeExceptionWrap
    def saveBynaryObj(self, obj: bytes, imageId: str, setName: str=None) -> None:
        """
        Save image in cache storage.

        Args:
            obj: binary representation of obj.
            imageId: unique id of image.
            setName: name of the collection where to save the image.
        """
        self.api.put(data={'binary': obj}, key=imageId, set_=setName)

    @aerospikeExceptionWrap
    def checkBynaryObj(self, objId: str, setName: str=None) -> bool:
        """
        Check image exists in bucket.

        Args:
            objId: unique id of obj.
            setName: name of the collection where to search for the obj.

        Returns:
            true if image exists, else false
        """
        obj = self.api.get(objId, setName)
        return obj is not None

    @aerospikeExceptionWrap
    def getBynaryObj(self, objId: str, setName: str=None) -> Union[None, bytes]:
        """
        Search image in bucket.

        Args:
            objId: unique id of obj.
            setName: name of the collection where to search for the obj.

        Returns:
            binary representation of obj if obj exists otherwise return none.
        """
        obj = self.api.get(objId, setName)
        if obj is not None:
            return obj.get('binary')

    @aerospikeExceptionWrap
    def deleteBynaryObj(self, objIds: List[str], setName: str=None) -> None:
        """
        Delete image from cache.

        Args:
            objIds: list of obj id.
            setName: name of the collection where to search for the obj.
        """
        for obj in objIds:
            self.api.remove(obj, setName)


def parseHosts(hosts: List[str]) -> List[Tuple[str, int]]:
    """
    Convert list of hosts in string representation to valid format for aerospike

    Args:
        hosts:
            list of hosts for aerospike cluster
    Returns:
        valid cluster structure for aerospike python lib
    """
    def convert(host):
        host = host.split(':')
        if len(host) == 2:
            return host[0], int(host[1])
        else:
            return host[0], int(host[1]), host[2]
    return [convert(i) for i in hosts]
