Installation and setup
======================

Surroundings
------------

Administration panel service operates with Windows 10 and CentOS 7 (other OS have not been tested).

Following software is required for administration panel service installation:

- PostgreSQL developer package;
- PostgreSQL DBMS instance (not recommended use LUNA API database);
- Python 3.5 or newer;
- Python setuptools.


For more details about each component installation, please refer to the LUNA API documentation.

Installation
------------

Before beginning, make sure you have LUNA Core and LUNA API up and functional. First, install Python dependencies by performing the following command:

.. code-block:: bash

	python setup.py install

In this case, versioning is based on git.  If the project is not cloned, use the following command:

.. code-block:: bash

	pip install -r requirements.txt

Note: the virtual environment is strongly recommended for installation. 
	

Configuration
-------------

All configurations are in configs/config.py file. You can change the file according to your needs or create your file.

Note: all options except garbage collectors must be synchronized with LUNA API options.

.. literalinclude:: ../../../luna_admin/configs/config.conf


Database creation
-----------------

After dependencies are installed, and all settings are configured, it is necessary to create a database (for more details \
refer to LUNA API documentation). Next, create a table using *db_create.py* script. The command is the following:

.. code-block:: bash

	python ./bases_scripts/db_create.py --config=./configs/myconfig.conf

The last command creates table in db, required for future service migration.

Graphana dashboards creation
----------------------------

For statistics visualization, you can use pre-arranged dashboards. To create one, run the commands:


.. code-block:: bash

	python ./luna_admin/create_grafana_dashboards.py --config=./configs/myconfig.conf


Grafana dashboard creation is optional. 


Startup
-------

If all previous steps were performed successfully, a server is ready to work. Run the script *run.py*\
to start the server. When launching, you can add such arguments as port and workes'\
amount. By default, the servers listen the ports 5010 and 5011 and uses one worker. Example \
of the startup string:

.. code-block:: bash

	./luna-admin/run.py --config="./configs/myconf.conf" --service_type=admin_backend

.. code-block:: bash

	./luna-admin/run.py --config="./configs/myconf.conf" --service_type=admin_task