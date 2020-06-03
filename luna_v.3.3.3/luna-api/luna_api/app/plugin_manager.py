from pluginbase import PluginBase
from plugins.list_enable_plugins import ENABLE_PLUGINS
from pluginbase import _shutdown_module

#: temporary storage of callback functions
SETTER_PORTRAITS_PLUGINS_ = []
GETTER_PORTRAITS_PLUGINS_ = []
ADMIN_STATISTICS_PLUGINS_ = []
ACCOUNT_STATISTICS_PLUGINS_ = []

#: list of callback functions
LIST_NAME_CALLBACK_FUNCTION = {"save_portrait": SETTER_PORTRAITS_PLUGINS_,
                               "get_portrait": GETTER_PORTRAITS_PLUGINS_,
                               "send_admin_statistics": ADMIN_STATISTICS_PLUGINS_,
                               "send_account_statistics": ACCOUNT_STATISTICS_PLUGINS_}


def loadPlugins():
    """
    Plug-in download function.
    
    :return: Result of make_plugin_source
    """
    plugin_base = PluginBase(package = 'app.plugins')
    plugin_source = plugin_base.make_plugin_source(
        searchpath = ['./plugins'])
    return plugin_source


def register_plugin_callback(dictNameFunc):
    """
    Callback function, which is transfered by *setup* method of plug-in and loads all necessary functions from plug-in.
        
    note: plug-in must call this function in *setup* method.
            
    >>> register_plugin_callback({"save_portrait": save_visionlabs_portrait, "get_portrait": get_visionlabs_portrait})
    
    :param dictNameFunc: dictionary with allowable keys: "save_portrait", "get_portrait", "send_admin_statistics",\
        "send_account_statistics".
    """
    for nameCallback in LIST_NAME_CALLBACK_FUNCTION:
        if nameCallback in dictNameFunc:
            LIST_NAME_CALLBACK_FUNCTION[nameCallback].append(dictNameFunc[nameCallback])


def registerCallbackFunctionsOfPlugin(pluginModule):
    """
    Function to register downloads of callback functions from plug-in. Function calls *setup* method from plug-in.

    :param pluginModule: 
    """
    pluginModule.setup(register_plugin_callback)


plugin_source = loadPlugins() #: initiate plug-in download


for enablePlugin in ENABLE_PLUGINS:
    with plugin_source:
        plug = plugin_source.load_plugin(enablePlugin)
        try:
            registerCallbackFunctionsOfPlugin(plug) #: register callback function
        except Exception as e:
            print(str(e))
            _shutdown_module(plug)

#: copy downloaded functions to persistent storage
SETTER_PORTRAITS_PLUGINS = SETTER_PORTRAITS_PLUGINS_
GETTER_PORTRAITS_PLUGINS = GETTER_PORTRAITS_PLUGINS_
ADMIN_STATISTICS_PLUGINS = ADMIN_STATISTICS_PLUGINS_
ACCOUNT_STATISTICS_PLUGINS = ACCOUNT_STATISTICS_PLUGINS_