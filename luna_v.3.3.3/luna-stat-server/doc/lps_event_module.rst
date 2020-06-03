================
LPS Event module
================

Module collects LUNA event statistic.

----------
Parameters
----------

* `port` - port to start the HTTP-server

----
Logs
----

* `ss.lps_module` - module's core logger
    * `ss.lps_module.handlers` - requests handler's logger

---
API
---

.. automethod:: stat_service.modules.lps_events_module.handlers.EventsHandler.post
