============
Installation
============

=================
Packages and requirements installation example for CentOS
=================

For the Service operation, one needs to install the following dependencies:
    *	Python 3.6;
    *	Redis v. 3.2.3 or higher;
    *	InfluxDB v. 1.3.2 or higher;
    *	Additional library dependencies, listed in requirements.txt.

To install packages and requirements, one should:

    * Install python 3.6

    * Install InfluxDB. For this subsequently perform the following commands:

    1) Load InfluxDB by the command `wget https://repos.influxdata.com/centos/7Server/amd64/stable/influxdb-1.3.4.x86_64.rpm`;

    2) Install InfluxDB by the command `yum install influxdb-1.3.4.x86_64.rpm;

    3) Enable auto-start by the command `systemctl enable influxdb.service`;

    4) Start InfluxDB service by the command `service influxdb start`.


    *	Install Redis

    1) Install Redis by the command `yum install redis`;

    2) Enable Redis auto-start by the command `systemctl enable redis.service`;

    3) Start Redis service by the command `service redis start`.


    *	Install Python libraries:

    Note: Virtual environment is strongly recommended for installation.

    * Create a virtual environment by the command `python3.6 -m venv venv`;

    * Activate the virtual environment by the command `source ./venv/bin/activate` (for deactivation enter `deactivate`)

    * Go to the folder with the project `cd stat-server`

    * Install dependencies from the file `pip3.6 install -r requirements.txt`

Now the installation is complete and Events & Statitics service can be started.

=================
Setup and Startup
=================

To start Events & Statistics service, one should:

1) Check and change the service settings in the configuration file `./config.conf` (if necessary):

    * INFLUX_LOGIN="\<influx login>"

    * INFLUX_PASSWORD="\<influx password>"

    * INFLUX_DATABASE="\<influx database>"

    * INFLUX_URL="\<influx url>:\<influx port>"

    * REDIS_LOGIN="\<redis login>"

    * REDIS_PASSWORD="\<redis password>"

    * REDIS_DATABASE="\<redis database>"

    * REDIS_URL="\<redis url>:\<redis port>"

    * LPS_URL="\<Luna API url>:\<Luna API port>"

    * LPS_VERSION=\<Luna API version>

    * COOKIE_SECRET="\<some random value to encrypt users' cookies>"


2) Create Influx database by the `python db_create.py` script;

3) Start the service:

    * Launch the LUNA API Python Server Events service by the command `python run.py lpse --port 5009`. The service receives events from LUNA API on the 5009 port. Instead of 5009, you can assign any free port.

    * Start the Statistic Manager service by the command `python run.py sm --port 5008`. The Service provides subscription and statistics. Instead of `5008`, you can also assign any free port.

   Note: It is possible to start several services of both types.

-----
Tests
-----

1) Ensure that both services and LUNA API are running.

2) Check and, if necessary, change the service settings in the `./test/config.py` configuration file:

    * LUNA_API_URL="<Luna API url\>/\<Luna API version\>/"

    * SS_BASE_URL="\<Statistic Manager service IP\>:\<Statistic Manager service port\>"

3) Run tests by the command `python -m unittest test.test`

For further usage see ./demo/raml.html