"""
Common module for work with  settings
"""
from optparse import OptionParser
from typing import List, Tuple, Union
from urllib.parse import urlparse

from luna3.configurator.configurator import ConfiguratorApi


def setSettingsInImageStoreFormat(options: OptionParser, settingName: str,
                                  settingValue: Union[str, int, float, dict, list]) -> List[Tuple]:
    """
    Set image store setting in specific format.

    Args:
        options: options
        settingName: setting name
        settingValue: setting value

    Returns:
        List of tuples. First element of tuple is a name of setting, second element is value.
    Raises:
        ValueError: if settingName not found in the set of allowable values.
    """
    mapS3SettingNameToSettingName = {"region": "S3_REGION", "host": "S3_HOST",
                                     "aws_public_access_key": "S3_AWS_PUBLIC_ACCESS_KEY",
                                     "aws_secret_access_key": "S3_AWS_SECRET_ACCESS_KEY",
                                     "authorization_signature": "S3_AUTHORIZATION_SIGNATURE"}
    mapAerospikeSettingNameToSettingName = {"hosts": "AEROSPIKE_HOSTS",
                                            "namespace": "AEROSPIKE_NAMESPACE"}
    if settingName == "S3":
        for s3SettingName, s3SettingValue in settingValue.items():
            options.__setattr__(mapS3SettingNameToSettingName[s3SettingName], s3SettingValue)

    elif settingName == 'LUNA_IMAGE_STORE_STORAGE_TYPE':
        options.__setattr__("STORAGE_TYPE", settingValue)
    elif settingName == 'LUNA_IMAGE_STORE_CACHE_ENABLED':
        options.__setattr__("CACHE_ENABLED", settingValue)
    elif settingName == 'AEROSPIKE_INMEMORY':
        for aerospikeSettingName, aerospikeSettingValue in settingValue.items():
            if aerospikeSettingName == "hosts":
                aerospikeSettingValue = ["{}:{}".format(aerospike["host"], aerospike["port"]) for aerospike in
                                         aerospikeSettingValue]

                options.__setattr__(mapAerospikeSettingNameToSettingName[aerospikeSettingName], aerospikeSettingValue)
    else:
        raise ValueError


def setAddress(options: OptionParser, settingName: str, value: dict):
    """
    Get adress from dict and set option's attributes: origin and api_version

    Args:
        options: options
        settingName: setting name
        value: dict with protocol, host, port and api_version
    """
    options.__setattr__(settingName.replace('ADDRESS', 'ORIGIN'),
                        '{}://{}:{}'.format(value['protocol'], value['host'], value['port']))
    options.__setattr__(settingName.replace('ADDRESS', 'API_VERSION'), value['api_version'])


def pullConfigFromLunaConfigurator(options: OptionParser, configuratorUrl: str, serviceName: str):
    """
   Pull settings from luna-configurator and set them in the options.

    Args:
        options: container for options
        configuratorUrl: url to configurator (origin + api version)
        serviceName: service name
    """
    configuratorUrl = urlparse(configuratorUrl)
    origin = "{}://{}:{}".format(configuratorUrl.scheme, configuratorUrl.hostname, configuratorUrl.port)
    apiVersion = configuratorUrl.path.split("/")[1]
    confClient = ConfiguratorApi(origin, apiVersion)

    settings = confClient.pullConfig(serviceName, raiseError=True).json

    for settingName, value in settings.items():
        if settingName == 'DB_LUNA_ADMIN':
            for dbSettingName, dbSettingValue in value.items():
                options.__setattr__('DB_ADMIN_{}'.format(dbSettingName.upper()), dbSettingValue)
        elif settingName.startswith('DB_LUNA') or settingName == 'LUNA_API_DB':
            mapDBSettingNameToSettingName = {"type": "DB", "user_name": "USER_NAME", "password": "PASSWORD_DB",
                                             "name": "DB_NAME", "host": "DB_HOST", "port": "DB_PORT"}
            for dbSettingName, dbSettingValue in value.items():
                options.__setattr__(mapDBSettingNameToSettingName[dbSettingName], dbSettingValue)
        elif settingName in ('LUNA_IMAGE_STORE_PORTRAITS_ADDRESS', 'LUNA_IMAGE_STORE_WARPED_ADDRESS'):
            setAddress(options, settingName, value)
            options.__setattr__(settingName.replace('ADDRESS', 'BUCKET'), value['bucket'])
        elif settingName.endswith('_ADDRESS'):
            setAddress(options, settingName, value)
        elif settingName == 'ADMIN_STATISTICS_SERVER':
            mapDBSettingNameToSettingName = {'origin': 'ADMIN_STATISTICS_SERVER_ORIGIN',
                                             'database_name': 'ADMIN_STATISTICS_DATABASE_NAME'}
            for dbSettingName, dbSettingValue in value.items():
                options.__setattr__(mapDBSettingNameToSettingName[dbSettingName], dbSettingValue)
        elif settingName in ["S3", 'LUNA_IMAGE_STORE_STORAGE_TYPE', 'LUNA_IMAGE_STORE_CACHE_ENABLED',
                           'AEROSPIKE_INMEMORY'] and serviceName == "luna-image-store":
            setSettingsInImageStoreFormat(options, settingName, value)
        else:
            options.__setattr__(settingName, value)
