import os

from tornado import httpclient

from configs import config
from storage.aws_s3.s3 import S3
from app.app import logger


if config.CACHE_ENABLED:
    import aerospike
    from storage.aerospike_cache import AerospikeAPI, parseHosts


SUCCESS = 'SUCCESS'
ERROR = 'ERROR'


def checkCache() -> bool:
    """
    Check current configured cache subsystem.

    Returns:
        Cache subsystem status
    """
    return checkAerospike() if config.CACHE_ENABLED else True


def checkAerospike() -> bool:
    """
        Check configuration of aerospike db.
    Returns:
        Aerospike db configuration status.
    """
    msg = '[AEROSPIKE_HOSTS] Connecting to Aerospike cluster: {}'

    try:
        api = AerospikeAPI(hosts=parseHosts(config.AEROSPIKE_HOSTS))
    except aerospike.exception.AerospikeError:
        logger.exception(msg.format(ERROR))
        return False
    else:
        logger.debug(msg.format(SUCCESS))
        msg = '[AEROSPIKE_NAMESPACE] Namespace exists: {}'
        cluster = api.info_all('namespace/{}'.format(config.AEROSPIKE_NAMESPACE))
        if '{{{}}}'.format(config.AEROSPIKE_NAMESPACE) in str(cluster):
            logger.debug(msg.format(SUCCESS))
        else:
            logger.error(msg.format(ERROR))
            return False

    return True


def checkStorage() -> bool:
    """
    Check current configured storage subsystem.

    Returns:
        valid status of settings
    """
    if config.STORAGE_TYPE == 'LOCAL':
        return checkDiskStorage()
    elif config.STORAGE_TYPE == 'S3':
        return checkS3()
    else:
        logger.error('[STORAGE_TYPE] Storage type not selected')
        return False


def checkDiskStorage() -> bool:
    """
    Check disk storage settings.

    Returns:
        valid status of settings
    """
    msg = '[LOCAL_STORAGE] {}: {}'

    msg_dir_created = 'Folder is exist or creating'
    try:
        os.makedirs(config.LOCAL_STORAGE, exist_ok=True)
    except OSError:
        logger.error(msg.format(msg_dir_created, ERROR))
        return False
    else:
        logger.debug(msg.format(msg_dir_created, SUCCESS))

    msg_dir_privs = 'Has read and write privileges on directory'
    if os.access(config.LOCAL_STORAGE, os.W_OK) and os.access(config.LOCAL_STORAGE, os.R_OK):
        logger.debug(msg.format(msg_dir_privs, SUCCESS))
    else:
        logger.debug(msg.format(msg_dir_privs, ERROR))
        return False

    return True


def checkS3() -> bool:
    """
    Check connect and authorize on s3 storages.

    Returns:
        valid status of settings
    """
    if (config.S3_HOST and config.S3_AWS_PUBLIC_ACCESS_KEY and config.S3_AWS_SECRET_ACCESS_KEY
            and config.S3_AUTHORIZATION_SIGNATURE):
        msg = "[S3_SETTINGS] All S3 parameter provided {}"

        logger.debug(msg.format(SUCCESS))
    else:
        msg = "[S3_SETTINGS] Not all S3 parameter provided, see config file, {}".format(ERROR)
        logger.debug(msg)
        return False

    S3.initS3Module(config.S3_HOST, config.S3_AWS_PUBLIC_ACCESS_KEY,
                 config.S3_AWS_SECRET_ACCESS_KEY, config.S3_REGION, config.S3_AUTHORIZATION_SIGNATURE)
    s3Ctx = S3("GET", '', '')

    http_client = httpclient.HTTPClient()
    headers = s3Ctx.getHeaders()
    request = httpclient.HTTPRequest(url=s3Ctx.getUrl(),
                                     method=s3Ctx.method,
                                     headers=headers,
                                     request_timeout=config.REQUEST_TIMEOUT,
                                     connect_timeout=config.CONNECT_TIMEOUT,
                                     body=s3Ctx.body)
    response = http_client.fetch(request, raise_error=False)
    s3Status = response.code == 200

    msg = "[S3_SETTINGS] Connect and authorize on s3 storage {}"
    if s3Status:
        logger.debug(msg.format(SUCCESS))
        return True
    else:
        logger.error(response.body)
        logger.error(msg.format(ERROR))
        return False


def checkConnections() -> bool:
    """
    Check all base systems.

    Returns:
        valid status of settings
    """

    checks = [
        checkCache(),
        checkStorage()
    ]

    return all(checks)
