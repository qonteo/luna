.. _external-hosts:

Connect to external hosts
=========================

By default system using connection to external hosts for following tasks:

* Install dependencies.

- Getting and puting  portraits to amazon s3. If you do not use  this storage for portraits system would
  not connect to s3.

- Determination ip address of machine. This value is used for monitoring of the system. System use google dns server.
  You can change dns server in file */configs/config.py*. If system can not ip address it would be use "127.0.0.1".
