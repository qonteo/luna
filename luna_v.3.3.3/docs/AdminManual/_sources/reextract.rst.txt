Update neural network
=====================

You should re-extract all descriptors for update neural network. For the process of re-extracting descriptors need:

	* configurate new instance of LUNA Core with new neural network;

	* set correct value for *LUNA_REEXTRACT_URL*, settings of luna-image-store with warps in configuration file;

	* run task of request to resource */reextract* with method *POST*;

	* after re-extracting descriptors change value *LUNA_URL* in configuration file;

	* change *LUNA_URL* in configuration file of LUNA Api.

Recommendations. Don't use LUNA Api when re-extract in progress. It is impossible to pause the process
of re-extraction. You can only to stop the process and restart it. All descriptors which already are in new instance
LUNA Core would not re-extract again.

.. automodule:: luna_admin.app.handlers.reextract_handler
	:members:

