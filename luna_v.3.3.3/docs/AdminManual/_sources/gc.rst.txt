Garbage collectors
------------------

In common, garbage collectors are designed to:

	#) delete descriptors and reference portraits in accordance with the storage policy.


Starting garbage collectors
===========================

You can either launch:
	1) garbage collectors for all objects (descriptors, accounts);

	#) obsolete descriptors garbage collectors in a web-interface;

	#) accounts' lists garbage collectors in a web-interface;

	#) scheduled periodic tasks to clear the entire system. To schedule a periodic task, set the start time (START_GC_DESCRIPTORS_TIME = "HH:MM" in the config.conf file) and the periodicity
	   in days (TIMEOUT_GC_DESCRIPTORS = 7 in the config.conf file) for each garbage collector separately.

	If the parameter TIMEOUT_GC_DESCRIPTORS has zero or negative value, tasks are not performed at all. 
	
Obsolete descriptors garbage collectors
=======================================

This type of garbage collectors deletes all free descriptors (i.e., those, which are not attached to a person or a list) in accordance with the storage policy.  

Steps, that are performed by a garbage collector:

	1) All links to the non-existing objects (descriptors and persons) in the table *AccountObjectListObject* are deleted;

	#) All free descriptors are found;

	#) All free descriptors are consistently deleted from LUNA Core;

	#) All reference portraits are deleted (in case, the SEND_TO_LUNA_IMAGE_STORE flag was enabled);

	#) All free descriptors are removed from *postgresql*.

If a step is executed with an error, all subsequent steps for this account are not performed.

Note: Steps are carried out for each account independently.
