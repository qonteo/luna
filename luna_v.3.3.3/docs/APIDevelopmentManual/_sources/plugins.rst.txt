Plug-ins
========

Plug-ins allow to add user functions to replace/supplement some system functions.\
With plug-ins you can influence 4 functions:

* Save portrait from received image;

- Obtain portrait by descriptor id;

- Send administrator statistics for each event;

- Send account statistics for each event;

Plug-in is a python file, which realizes one or more functions listed above and with \
suitable signatures.

In script file you should realize *setup* method. This method receives function, which registers callback functions as an input.\
The function in its turn receives specialized dictionary as an input. This dictionary contains functions, which\
are called by occurrence of corresponding event.

+-------------------------------------------------------+-------------------------------------------+--------------+------------------------+
| Function                                              | Influence type                            | Realized     | Dictionary key         |
+=======================================================+===========================================+==============+========================+
| Save portrait from received image                     | In addition to current functionality      | PLUS         |save_portrait           |
+-------------------------------------------------------+-------------------------------------------+--------------+------------------------+
| Obtain portrait by descriptor id                      | In replace for current functionality      | PLUS         |get_portrait            |
+-------------------------------------------------------+-------------------------------------------+--------------+------------------------+
| Send administrator statistics for each event          |  In addition to current functionality     | MINUS        |send_admin_statistics   |
+-------------------------------------------------------+-------------------------------------------+--------------+------------------------+
| Send account statistics for each event                |  In addition to current functionality     | PLUS         |send_account_statistics |
+-------------------------------------------------------+-------------------------------------------+--------------+------------------------+

Plug-in installation
--------------------

To install plug-in you simply need to put it in *plugins* folder and add it to the list of active plug-ins. \
For plug-in activation add it to the list in *plugins.list_enable_plugins.py* file. Several plug-ins can
work simultaneously. For function "Obtain portrait by descriptor id" one function is called from  \
exact plug-in. All other functions are called in exact order from plug-ins, which correspond to current event.\

To activate plug-in usage in the application, set flag *ENABLE_PLUGINS=1* in *configs/config.conf* file.

Callback-function signature
---------------------------

Save portrait from received image 
.................................
    """
    Saving portrait to file.

    :param imgBytes: portrait.
    :param faces:   JSON, with face (see description of extraction response).
    :param isWarpedImage: flag that image is warped.
    :return: nothing

    """

Obtain portrait by descriptor id 
................................

    """
    Get portrait from disk.

    :param portraitId: id of descriptor.
    :rtype: tuple
    :return: * if found image - tuple (imgBytes, True).

             - if not found - tuple(None, False).

    """

Send account statistics
.......................

    """
    Send account statistics to other service

    :param statistics: json with stats (see :json:object:`statistic of account after failed matching`, :json:object:`statistic of account after success extract`, :json:object:`statistic of account after success matching`)
    :param request_id: request id
    :param logger: logger
    """

Plug-in example
---------------

The following plug-in receives and saves portrait on hard drive.


.. literalinclude:: ../../../luna_api/plugins/save_portrait_to_disk.py


.. literalinclude:: ../../../luna_api/plugins/send_account_statistics.py


Plug-in manager
---------------

Plug-in manager is based on PluginBase_ module. Module must be initialized when application is launched in app.__init__ .



.. _PluginBase: http://pluginbase.pocoo.org/

.. automodule:: luna_api.app.plugin_manager
    :members: