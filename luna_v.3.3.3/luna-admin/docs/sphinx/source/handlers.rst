Documentation of tornado-handlers
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   accounts_handlers
   account_handler
   lists_handler
   tokens_handler
   persons_handler
   version_handler
   config_handler
   search_handler
   tasks_handlers
   reextract
   internal_task_handler
   stats_handler
   grafana_handler

Common jsons
============

.. json:object:: server_error
    :showexample:

    :property error_code: inner error code, for more info about errors go to :ref:`errors-label`.
    :proptype error_code: integer
    :property detail: error description
    :proptype detail: string

.. json:object:: account_info
    :showexample:

    :property uuid4 account_id: account id
    :property email email: email of account
    :property organization_name organization_name: organization name
    :property boolean status: if account is currently blocked, system returns *True*

.. json:object:: account_stats
    :showexample:

    :property integer person_count: person count of account
    :property integer list_count: list count of account
    :property integer descriptor_count: descriptor count of account
    :property integer token_count: token count of account

.. json:object:: account
    :showexample:

    :property info: account info
    :proptype info: :json:object:`account_info`
    :property  stats: account stats
    :proptype stats: :json:object:`account_stats`

.. json:object:: luna_list
    :showexample:

    :property list_id: list id
    :proptype list_id: uuid4
    :property account_id: account id
    :proptype account_id: uuid4
    :property user_data: user data about list
    :proptype user_data: user_name
    :property integer count_object_in_list: object's count in list
    :property last_update_time: time of last action with list (attach or detach face from list)
    :proptype last_update_time: iso8601

.. json:object:: luna_person
    :showexample:

    :property person_id: person id
    :proptype person_id: uuid4
    :property faces: linked faces
    :proptype faces: _list_(uuid4)
    :property create_time: time of face creating
    :proptype create_time: iso8601
    :property user_data: user data about face
    :proptype user_data: user_name
    :property account_id: account id
    :proptype account_id: uuid4
.. json:object:: auth_token
    :showexample:

    :property token_id: token id
    :proptype token_id: uuid4
    :property token_data: token_data if auth is token else nothing
    :proptype token_data: street_address


.. json:object:: task_info
    :showexample:

    :property time duration: duration of task ("in progress" if not ended)
    :property target: target of task
    :proptype target:  _enum_(all)_(account)
    :proptype uuid4 task_id: target id
    :property integer error_count: error count
    :property float progress: task progress

.. json:object:: taskReextractDetails
    :showexample:

    :property integer re-extract descriptors: re-extract descriptors count

.. json:object:: taskGCOldDescriptorsDetails
    :showexample:

    :property integer count_delete_descriptors: removed descriptors count
    :property integer count_s3_errors: luna-image-store error count

.. json:object:: task_type
    :showexample:

    :property task_type: "removing old descriptors" or "re-extract descriptors"
    :proptype task_type:  _enum_(removing old descriptors)_(re-extract descriptors)
    :property taskDetail: detail of task
    :proptype taskDetail: _enum_(:json:object:`taskGCOldDescriptorsDetails`)_(:json:object:`taskReextractDetails`)
