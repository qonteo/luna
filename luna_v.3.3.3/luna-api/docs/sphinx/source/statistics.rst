Admin and accounts statistic
============================

After some request server send statistic with result of this request. There are two type of statistics: for a admin and \
for accounts. Dispatch of both statistics is regulated in parameters  of config-file  *SEND_ADMIN_STATS*  and \
*SEND_ACCOUNT_STATS*. Dispatch of statistics is made right away after request.



Statistic of administrator
--------------------------

This statistic is send to influxdb where it storage as a time series. Series can be created with scripts \
"base_scripts" corresponding config-file.

Data in statistics
..................

For success request
###################
+-------------------------+--------+------------------+-------------+----------------------------------------+
| Resource                | Method | Series           | Tags/Values | Description                            |
+=========================+========+==================+=============+========================================+
| Common                  |        |                  | Tags                                                 |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | resource    | One of: identify, search, verify,      |
|                         |        |                  |             | match or descriptors                   |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | server      | Ip of address of worker                |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | account_id  | id of account                          |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | Value                                                |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | value_time  | time of request                        |
+-------------------------+--------+------------------+-------------+----------------------------------------+
|'/matching/identify'     | POST   | matching_success | Tags                                                 |
|                         |        |                  +-------------+----------------------------------------+
|'/matching/verify'       |        |                  | limit       | result count in answer                 |
|                         |        |                  +-------------+----------------------------------------+
|'/matching/search'       |        |                  | template    | 0 or 1 (template is person or not)     |
|                         |        |                  +-------------+----------------------------------------+
|'/matching/match'        |        |                  | candidate   | 0 or 1, matching by dynamic list or    |
|                         |        |                  |             | account list                           |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | Values                                               |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | value_sim   | value of most similarity descriptor    |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | value_time  | time of request                        |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | value_size  | luna list or persons or descriptors    |
|                         |        |                  |             | count                                  |
+-------------------------+--------+------------------+-------------+----------------------------------------+
|'/storage/descriptors'   | POST   | extract_success  | Tags                                                 |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | count_faces | count of faces on image                |
+-------------------------+--------+------------------+-------------+----------------------------------------+

For failed request
##################

+-------------------------+--------+------------------+-------------+----------------------------------------+
| Resource                | Method | Series           | Tags/Values | Description                            |
+=========================+========+==================+=============+========================================+
| Common                  |        | errors           | Tags                                                 |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | resource    | One of: identify, search, verify,      |
|                         |        |                  |             | match or descriptors                   |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | server      | Ip of address of worker                |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | account_id  | id of account (if exist                |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | Values      |                                        |
|                         |        |                  +-------------+----------------------------------------+
|                         |        |                  | error_code  | Error code                             |
+-------------------------+--------+------------------+-------------+----------------------------------------+

Statistic of accounts
---------------------

This statistic is send to external service corresponding config-file. It is http request with json.



Data in statistics
..................

.. json:object:: template
    :showexample:

    :propery person_id: person id
    :proptype person_id: uuid4
    :propery descriptor_id: person id
    :proptype descriptor_id: uuid4


.. json:object:: candidate
    :showexample:

    :property list_id: list id
    :proptype list_id: uuid4
    :property list_data: list id
    :proptype list_data: street
    :property list_type: list id
    :proptype list_type: _enum_(0,1)
    :property person_ids: list id of persons
    :proptype person_ids: _list_(uuid4)
    :property descriptor_ids: list id of persons
    :proptype descriptor_ids: _list_(uuid4)


.. json:object:: statistic of account after success matching
    :showexample:

    :property account_id: id of account
    :proptype account_id: uuid4
    :property timestamp: statistics creation time.
    :proptype timestamp: integer
    :property result: request reply, for example `identify_result`.
    :proptype result: :json:object:`identify_result`
    :property source: one of: "match, search, identify, verify"
    :proptype source: 'match'
    :propery authorization: authorization, "basic" or :json:object:`auth_token`
    :proptype authorization: :json:object:`auth_token`
    :property template: one of field "person_id" or "descriptor_id" from :json:object:`template`
    :proptype template: :json:object:`template`
    :property candidate: one of field "list_id", "person_ids" or "descriptor_ids" from :json:object:`candidate`
    :proptype candidate: :json:object:`candidate`

.. json:object:: statistic of account after failed matching
    :showexample:

    :property account_id: id of account
    :proptype account_id: uuid4
    :property timestamp: statistics creation time
    :proptype timestamp: integer
    :property result: request reply, for example `identify_result`.
    :proptype result: :json:object:`server_error`
    :property source: one of: "match, search, identify, verify"
    :proptype source: 'match'
    :propery authorization: authorization, "basic" or :json:object:`auth_token`
    :proptype authorization: "basic"
    :property template: one of field "person_id" or "descriptor_id" from :json:object:`template`
    :proptype template: :json:object:`template`
    :property candidate: one of field "list_id", "person_ids" or "descriptor_ids" from :json:object:`candidate`
    :proptype candidate: :json:object:`candidate`


.. json:object:: statistic of account after success extract
    :showexample:

    :property account_id: id of account
    :proptype account_id: uuid4
    :property timestamp: statistics creation time
    :proptype timestamp: integer
    :property result: request reply
    :proptype result: :json:object:`extract_result`
    :property source: "descriptors"
    :proptype source: 'descriptors'
    :propery authorization: authorization, "basic" or :json:object:`auth_token`
    :proptype authorization: "basic"


.. automodule:: luna_api.app.admin_stats
	:members:

.. automethod:: luna_api.app.rest_handlers.storage_handlers.StorageHandler.generateAccountStats

.. automethod:: luna_api.app.rest_handlers.storage_handlers.StorageHandler.generateAdminStatisticsRequestBody

.. automethod:: luna_api.app.rest_handlers.storage_handlers.StorageHandler.setAdditionalDataToAdminStatistic

.. automethod:: luna_api.app.rest_handlers.matcher_handler.MatcherHandler.setAdditionalDataToAdminStatistic

.. automethod:: luna_api.app.rest_handlers.photo_handler.PhotoHandler.setAdditionalDataToAdminStatistic

.. automethod:: luna_api.app.rest_handlers.storage_handlers.StorageHandler.setAdditionalDataToAccountStatistic

.. automethod:: luna_api.app.rest_handlers.matcher_handler.MatcherHandler.setAdditionalDataToAccountStatistic

.. automethod:: luna_api.app.rest_handlers.storage_handlers.StorageHandler.sendStats

.. automethod:: luna_api.app.rest_handlers.matcher_handler.MatcherHandler.sendStats

.. automethod:: luna_api.app.rest_handlers.matcher_handler.MatcherHandler.on_finish

.. automethod:: luna_api.app.rest_handlers.photo_handler.PhotoHandler.on_finish

