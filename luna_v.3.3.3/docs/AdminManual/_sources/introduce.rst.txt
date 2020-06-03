Introduction
============

LUNA Administration Panel service is created for LUNA API administration and data consistency maintenance in LUNA Core and LUNA API.


Features
--------

Account overview
................

The administrator can either review all accounts in the system or each account separately.

Accounts' blocking
..................

Any account in the system can be blocked or unblocked. After account is blocked, all actions, except 
browsing the statistics (amount of persons, lists and so forth), are restricted.

Garbage collectors
..................

This module is designed to:

	1) delete obsolete descriptors, that are not attached to any person or list. LUNA architecture implies that such descriptors (and reference portraits) are deleted after their TTL (time-to-live) expires. 
	   One can control descriptors deletion by the settings (TTL period, time and periodicity of deletion). You can launch the operations for all accounts or each account separately;

Access
------

You can access the Panel in the *Chrome* browser. By default, the service is accessible at
*http://127.0.0.1:5010*. Login and password: *root/root*.
