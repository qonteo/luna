import configparser
from configparser import ConfigParser
import os


class ConfigLoader:

    config = ConfigParser(interpolation=configparser.ExtendedInterpolation())
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config.read(os.path.join(root_dir, 'resources', 'configs.conf'))
    local_config_path = os.path.join(root_dir, 'resources', 'local.conf')
    if os.path.exists(local_config_path):
        config.read(local_config_path)

    @staticmethod
    def get_property(key):
        return ConfigLoader.config.get('Common', key)

    @staticmethod
    def get_int_property(key):
        return int(ConfigLoader.get_property(key))

    @staticmethod
    def get_db_url():
        return {
            'dbType': ConfigLoader.get_property('dbType'),
            'dbName': ConfigLoader.get_property('dbName'),
            'dbHost': ConfigLoader.get_property('dbHost'),
            'dbPort': ConfigLoader.get_property('dbPort'),
            'dbUser': ConfigLoader.get_property('dbUser'),
            'dbPass': ConfigLoader.get_property('dbPass')
        }

    @staticmethod
    def get_api_url():
        return ConfigLoader.get_property('lps_url')

    @staticmethod
    def get_admin_url():
        return ConfigLoader.get_property('admin_url')

    @staticmethod
    def get_luna_core_url():
        return ConfigLoader.get_property('luna_core_url')

    @staticmethod
    def get_selenium_url():
        return ConfigLoader.get_property('selenium_url')



