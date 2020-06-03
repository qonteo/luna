Versioning
==========
Versioning is realized in python-versioneer_ script. For versioning launch setup.py file
with install parameter. All version information will be saved in file */app/Luna_python_server.egg-info/PKG-INFO*. Simultaneously
*version.py* file with value of *VERSION* variable will be created. Example:

*VERSION={"Version": {"api": 1, "major": "0", "minor": "0", "patch": "1"}}*

*VERSION={"Version": "UNKNOWN"}*

If all dependencies are already installed and you only need to conduct \
versioning, launch script *versioneer.py* with *version* parameter from root folder. \
Note that for versioning you need *git* files.

.. _python-versioneer: https://github.com/warner/python-versionee

.. automodule:: app.rest_handlers.version_handler
    :members:

.. automodule:: versioneer
    :members:
