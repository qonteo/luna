Installation
============
For proper installation you need to clone project from git.

Surroundings
------------

The service can be installed on Windows 10 and CentOS 7 (not tested on other system versions).

Required predefined dependencies:

* Developer package postgresql (for psycopg2 installation), in CentOS 7 you can execute following command:

.. code-block:: bash

	yum install postgresql-server gcc python34-devel file postgresql postgresql-devel

- Python v. 3.5 or higher is required.
- It is strongly recommended to create virtual surroundings for python dependencies installation.
- Python setuptools module can be installed via pip (pip install setuptools).


Dependencies installation
-------------------------

After surroundings installation launch *setup.py* with *install* parameter. If surrounding is installed correctly, this script\
will install all dependencies and carry out versioning automatically. 

If all dependencies are already installed and only versioning is required, \
launch *versioneer.py* script with *version* parameter from root folder. \
Please note that for versioning *git* files are required.

If you need to install dependencies without versioning, you should use dependencies file \
placed in *luna_api/luna_api.egg-info*

```
pip install -r "requires.txt
```


Configuration
-------------
After dependencies installation configuration file should be set. File is placed in *"/configs/config.conf"*.\

Database creation
-----------------
All databases for service must be created in accordance with *"/configs/config.conf"*.

- Postgresql (require version 9.5 or higher)

Create all required schemes in *postgresql*. For that create table with user name from \
*config.conf*, then launch *base_scripts/db_create.py* script. If script was executed without errors, \
all schemes were created successfully. Restarting the script will lead to errors, indicating that in this table schemes \
already exist. db_create also creates scripts for further database migration (db_repository folder), without \
these scripts db_migrate script execution is impossible.

If table or user is not yet created, you should execute following commands:

.. code-block:: sql

	psql -U postgres;
	create role faceis;
	ALTER USER faceis WITH PASSWORD 'faceis';
	CREATE DATABASE faceis_db;
	GRANT ALL PRIVILEGES ON DATABASE faceis_db TO faceis;
	ALTER ROLE faceis WITH LOGIN;


- S3

For S3 usage you should create *bucket* from *config.conf*. To do this, launch script\
*base_scripts/s3_bucket_create.py*. Note that this script doesn't check if *bucket* already exists or not.

- Influx (require version 1.3 or higher)

For Influx DB creation you should launch *base_scripts/influx_db_create.py* script.
**Attention: influxdb are limited for records count by default**. For unlimited records set *max-series-per-database*
and *max-values-per-tag* in influx config in 0.

First launch and testing
------------------------
If all previous actions are executed successfully, server is ready to work. To start server please launch *run.py*
script from directory "luna_api". While start you can add arguments: server message port and number of workers,
servicing the server. By default 5000 port is used and one worker is launched.
Example:

.. code-block:: bash

	./run.py --workers 8 --port 5000

After server is started, testing is recommended. To perform testing execute the following command from root directory

.. code-block:: bash

	python -m unittest tests.unittests_main

from folder, where file *run.py* is placed. All tests should perform successfully.

