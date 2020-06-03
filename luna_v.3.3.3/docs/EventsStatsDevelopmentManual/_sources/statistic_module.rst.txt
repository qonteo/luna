================
Statistic module
================


This module allows sharing statistics to users.

The module consists of the following components:

* **EventDeliveryService** registers the listeners and deliveres Redis messages (if not filtered out);

* **LPSUserAuthService** checks user LPS authorization;

* **StatService** shares InfluxDB statistics.

----------
Parameters
----------

* `port` - port to start the HTTP-server.

----
Logs
----

* `ss.stat_module` - core module logger
    * `ss.stat_module.service` - module services' core logger
        * `ss.stat_module.service.eds` - **EventDeliveryService** logger
        * `ss.stat_module.service.lps_auth` - **LPSUserAuthService** logger
        * `ss.stat_module.service.ss` - **StatService** logger
    * `ss.stat_module.handler` - requests handlers' core logger
        * `ss.stat_module.handler.events` - requests handler's logger for `/api/events` 
        * `ss.stat_module.handler.subscribe` - requests handler's logger for `/api/subscribe` 

