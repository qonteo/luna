Service launch
==============

Example of service launch from root directory:

	*python run.py --workers=4 --port=5001*

Parameters *workers=1* and *port=5000* are default ones. Note, that python version should be 3.5. or higher.

During server launch connections to *luna, s3, postgres* are checked. Connection to *s3* is checked only\
if option is activated in config.

.. automodule:: luna_api.run
	:members:

