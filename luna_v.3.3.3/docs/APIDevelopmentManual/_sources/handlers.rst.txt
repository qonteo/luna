Documentation of tornado-handlers
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   account_api
   tokens
   token
   persons
   lists
   photo
   matching
   descriptor
   link_descriptor_to_list
   person_api
   person_link_descriptor
   person_link_list
   version
   registration
   storage_api


Json's
------

.. json:object:: user_data
   :showexample:

   :property user_data: person information
   :proptype user_data: user_name


.. json:object:: token_data
   :showexample:

   :property token_data: token information
   :proptype token_data: street_address


.. json:object:: list_data
   :showexample:

   :property list_data: list information
   :proptype list_data: city


.. json:object:: server_error
    :showexample:

    :property error_code: inner error code, for more info about errors go to :ref:`errors-label`.
    :proptype error_code: integer
    :property detail: error description
    :proptype detail: string


.. json:object:: person
   :showexample:

   :property user_data: person information
   :proptype user_data: user_name
   :property id: person id
   :proptype id: uuid4
   :property descriptors: list of descriptors, linked to person.
   :proptype descriptors: _list_(uuid4)
   :property create_time: person creation time with timezone
   :proptype create_time: iso8601
   :property lists: list of accounts list ids, person is linked to.
   :proptype lists: _list_(uuid4)


.. json:object:: descriptor
   :showexample:

   :property id: descriptor id
   :proptype id: uuid4
   :property person_id: descriptor id, person is linked to (null, if descriptor is not linked to any person)
   :proptype person_id: uuid4
   :property last_update: time of last descriptor attach/detach to lists, persons
   :proptype last_update: iso8601
   :property lists: list of account list ids descriptor is linked to
   :proptype lists: _list_(uuid4)


.. json:object:: account_list
   :showexample:

   :property id: list id
   :proptype id: uuid4
   :property count: number of objects in the list
   :proptype count: integer
   :property list_data: list data
   :proptype list_data: city


.. json:object:: rect
   :showexample:

   :property height: Rectangle height
   :proptype height: integer
   :property width: Rectangle width
   :proptype width: integer
   :property x: Top left corner x coordinate
   :proptype x: integer
   :property y: Top left corner y coordinate
   :proptype y: integer

.. json:object:: estimation_emotions

   :property anger: Anger probability.
   :proptype anger: float
   :property disgust: Disgust probability.
   :proptype disgust: float
   :property fear: Fear probability.
   :proptype fear: float
   :property happiness: Happiness probability.
   :proptype happiness: float
   :property neutral: Neutral probability.
   :proptype neutral: float
   :property sadness: Sadness probability.
   :proptype sadness: float
   :property surprise: Surprise probability.
   :proptype surprise: float


.. json:object:: estimation_ethnicities

   :property asian: asian ethnicity probability
   :proptype asian: float
   :property indian: indian ethnicity probability
   :proptype indian: float
   :property caucasian: caucasian ethnicity probability
   :proptype caucasian: float
   :property african: african american ethnicity probability.
   :proptype african: float

.. json:object:: head_pose

   :property yaw: yaw rotation in degrees
   :proptype yaw: integer
   :property pitch: pitch rotation in degrees
   :proptype pitch: integer
   :property roll: roll rotation in degrees
   :proptype roll: integer


.. json:object:: attributes
   :showexample:

   :property age: Age estimation (in years, number - minimum: 0 - maximum: 100)
   :proptype age: integer
   :property gender: Gender estimation ( minimum: 0 - maximum: 1)
   :proptype gender: integer
   :property eyeGlasses: Estimates whether the persons wears eye glasses ( minimum: 0 - maximum: 1)
   :proptype eyeGlasses: float
   :property emotions: Face emotions estimation.
   :proptype emotions: :json:object:`estimation_emotions`
   :property ethnicities: Ethnicities estimation.
   :proptype ethnicities: :json:object:`estimation_ethnicities`
   :property head_pose: Head pose estimation.
   :proptype head_pose: :json:object:`head_pose`

.. json:object:: qualityAttributes
   :showexample:

   :property light: Low value means overlit face area (i.e. overbright lighting, sensor overexposure), minimum: 0 - maximum: 1.
   :proptype light: float
   :property dark: Low value means underlit face area (i.e. due to backlight, poor lighting, sensor underexposure), minimum: 0 - maximum: 1.
   :proptype dark: float
   :property saturation: Low value means low saturation (e.g. grayscale images), minimum: 0 - maximum: 1.
   :proptype saturation: float
   :property blurriness: Low value means blurred image (e.g. due to depth of field or motion blur). High value means sharp image, minimum: 0 - maximum: 1.
   :proptype blurriness: float


.. json:object:: exif
   :showexample:

   :property artist: Artist tag
   :proptype artist: user_name
   :property dateTime: Date, time tag
   :proptype dateTime: iso8601


.. json:object:: extract_one_descriptor
   :showexample:

   :property id: descriptor id
   :proptype id: uuid4
   :property rect: Bounding rectangle
   :proptype rect: :json:object:`rect`
   :property rectISO: Bounding rectangle
   :proptype rectISO: :json:object:`rect`
   :property score: Face detection confidence (number - minimum: 0 - maximum: 1)
   :proptype score: float
   :property quality: Image quality estimation
   :proptype quality: :json:object:`qualityAttributes`
   :property attributes: Face attributes
   :proptype attributes: :json:object:`attributes`


.. json:object:: one_match_result_person
   :showexample:

   :property person_id: person id with linked best match descriptor
   :proptype person_id: uuid4
   :property similarity: similarity
   :proptype similarity: float
   :property user_data: person data
   :proptype user_data: user_name
   :property descriptor_id: descriptor id with best match to person, descriptor id is linked to.
   :proptype descriptor_id: uuid4


.. json:object:: one_match_result_descriptor
   :showexample:

   :property id: descriptor id
   :proptype id: uuid4
   :property similarity: similarity
   :proptype similarity: float

.. json:object:: auth_token
    :showexample:

    :propery token_id: token id
    :proptype token_id: uuid4
    :propery token_data: token_data if auth is token else nothing
    :proptype token_data: street_address

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
