Error codes
===========
|Error                                   |Error code|Error description                                                          |
|----------------------------------------|----------|---------------------------------------------------------------------------|
|BadConfig                               |100       |Bad/incomplete configuration {}                                            |
|BadQuery                                |101       |Bad/incomplete query {}                                                    |
|BadBody                                 |102       |Bad/incomplete body {}                                                     |
|OutOfMemoryError                        |104       |Out of memory {}                                                           |
|GenericError                            |200       |Generic error {}                                                           |
|PutRecord                               |1000      |Failed to put DB record {}                                                 |
|GetRecord                               |1001      |Failed to get DB record {}                                                 |
|TouchRecord                             |1002      |Failed to touch DB record {}                                               |
|DelRecord                               |1003      |Failed to delete DB record {}                                              |
|AppendRecord                            |1004      |Failed to append to DB record {}                                           |
|SerializeObject                         |1008      |Failed to serialize object {}                                              |
|DeserializeObject                       |1009      |Failed to deserialize object {}                                            |
|OutOfMemory                             |1010      |Out of memory {}                                                           |
|BadMessage                              |2000      |Bad/incomplete message package {}                                          |
|CoreBadContentType                      |2001      |Bad/unsupported message content type {}                                    |
|WorkerCallFailed                        |2002      |Failed to call a remote worker {}                                          |
|CreateImage                             |3000      |Failed to create image {}                                                  |
|DecodeImage                             |3001      |Failed to decode image data {}                                             |
|ImageSize                               |3002      |Incorrect image size {}                                                    |
|CreateObject                            |4000      |Failed to create FSDK object {}                                            |
|DetectFeatureSet                        |4001      |Failed to detect a feature set {}                                          |
|DetectFace                              |4002      |Failed to detect a face {}                                                 |
|NoFaces                                 |4003      |No faces found {}                                                          |
|MultipleFaces                           |4004      |Multiple faces found {}                                                    |
|BadInput                                |4005      |Bad/incomplete input data {}                                               |
|ConvertImage                            |4007      |Failed to convert image format {}                                          |
|EstimateAttributes                      |4009      |Failed to estimate face image attributes {}                                |
|DescriptorQuality                       |4010      |Descriptor quality is too low {}                                           |
|ExtractDescriptor                       |4011      |Failed to extract a descriptor {}                                          |
|MatchCreateObject                       |5001      |Failed to create FSDK object {}                                            |
|MatchAppendToBatch                      |5002      |Failed to add descriptor to batch {}                                       |
|MatchDescriptors                        |5003      |Failed to match descriptors {}                                             |
|MatchBadInput                           |5004      |Bad/incomplete input data {}                                               |
|ListBadInput                            |6000      |Bad/incomplete input data {}                                               |
|ListBadMode                             |6001      |Unknown operation mode {}                                                  |
|LunaServerError                         |7004      |Internal server error {}                                                   |
|LunaCoreConnectionTimeout               |9001      |Network error Connection timeout to LUNA Core                              |
|LunaCoreRequestTimeout                  |9002      |Network error Request timeout to Luna Core                                 |
|LunaCoreRequestError                    |9003      |Unknown error {} request failed. error_code: {} detail: {}                 |
|GetConnectionToDBError                  |10001     |Database error Connection to database is refused                           |
|CreateQueryError                        |10002     |Database error Creating sql request failed                                 |
|ConnectionClosed                        |10013     |Database error Connection to database is closed                            |
|ExecuteError                            |10015     |SQL error Execute sql request failed                                       |
|AccountNotFound                         |11002     |Authorization failed Account corresponding login/password not found        |
|AccountIsNotActive                      |11004     |Account is suspended Account is suspended                                  |
|MatchingResultEmpty                     |11007     |Matching errors Empty matching result                                      |
|NoPhotoToMatching                       |11008     |Matching errors No descriptors for matching                                |
|RequestInternalServerError              |11009     |Internal server error Internal server error                                |
|EmailExist                              |11011     |Unique constraint error An account with given email already exists         |
|ManyFaces                               |11012     |Extract policy error Too many faces found                                  |
|IncorrectEmail                          |11013     |Bad/incomplete input data Invalid email address                            |
|PasswordBadLength                       |11014     |Bad/incomplete input data                                                  |
|BigUserData                             |11015     |Bad/incomplete input data Max length user data is 128 symbols              |
|LinkDescriptorAlreadyExist              |11016     |Unique constraint error                                                    |
|DescriptorNotFound                      |11018     |Object not found Descriptor not found                                      |
|AccountListNotFound                     |11019     |Object not found Account list not found                                    |
|ObjectNotFound                          |11020     |Object not found One or more {} not found                                  |
|TokenNotFound                           |11022     |Object not found Token not found                                           |
|PortraitNotFound                        |11024     |Object not found Portrait not found                                        |
|UnknownErrorFromLunaFaces               |11025     |Internal server error Unknown error from luna faces                        |
|BadFormatUUID                           |12001     |Bad/incomplete input data                                                  |
|RequestNotContainsJson                  |12002     |Bad/incomplete input data Request does not contain json                    |
|FieldNotInJSON                          |12003     |Bad/incomplete input data Field {} not found in json                       |
|BadTypeOfFieldInJSON                    |12004     |Bad/incomplete input data Field {} must be {}                              |
|EmptyJson                               |12005     |Bad/incomplete input data Request contain empty json                       |
|EmptyField                              |12009     |Bad/incomplete input data Empty field {}                                   |
|BadHeaderAuth                           |12010     |Bad/incomplete input data                                                  |
|BadQueryParams                          |12012     |Bad/incomplete input data Bad query parameters {}                          |
|PageNotFoundError                       |12013     |Resource not found Page not found                                          |
|QueryParameterNotFound                  |12014     |Bad/incomplete input data Required parameters {} not found                 |
|RequiredQueryParameterNotFound          |12016     |Bad/incomplete input data No one parameters {} not found                   |
|BadContentType                          |12017     |Bad/incomplete input data Bad content type                                 |
|UnsupportedQueryParm                    |12018     |Bad/incomplete input data Unsupported param {}                             |
|BadAuthParam                            |12019     |Bad/incomplete input data Bad format of authorization header               |
|AuthFailedError                         |12020     |Bad/incomplete input data Unknown error authorization                      |
|MethodNotAllowed                        |12021     |Method not allowed Method not allowed                                      |
|BadInputJson                            |12022     |Bad/incomplete input data                                                  |
|NotAcceptable                           |12023     |Bad/incomplete input data Not Acceptable                                   |
|UnsupportedMediaType                    |12024     |Bad/incomplete input data Unsopported media type                           |
|SpecifiedTypeNotMatchDataType           |12025     |Bad/incomplete input data                                                  |
|BadInputXPK                             |12026     |Bad/incomplete input data Failed to parse XPK                              |
|RequestLunaImageStoreError              |13002     |Internal server error Request to luna-image-store failed                   |
|ImageNotFoundError                      |13003     |Object not found Image not found                                           |
|ImageCountExceededLimit                 |13004     |Bad/incomplete input data Image count exceeded limit 1000                  |
|BucketNotFound                          |13005     |Object not found Bucket not found                                          |
|BucketAlreadyExist                      |13006     |Unique constraint error Bucket already exist                               |
|ObjectInBucketNotFound                  |13007     |Object not found Object not found                                          |
|ObjectInBucketAlreadyExist              |13008     |Unique constraint error Object already exist                               |
|ObjectInBucketCountExceededLimit        |13009     |Bad/incomplete input data Object count exceeded limit 1000                 |
|ErrorGetPortraitPlugin                  |14001     |Plugin error Failed get portrait from plugin                               |
|ErrorSavePortraitPlugin                 |14002     |Plugin error Failed save portrait to plugin                                |
|ReExtractExceedMaximumIteration         |16008     |Internal server error Exceed maximum iteration count                       |
|TaskNotFound                            |16009     |Object not found Task not found                                            |
|RequestToTaskServerTornadoError         |16010     |Internal server error Request to task server failed                        |
|CheckConnectionToReExtractBroker        |16011     |Internal server error                                                      |
|InfluxConnectionTimeout                 |17001     |Internal server error Connection timeout to influxdb                       |
|ConvertBase64Error                      |18001     |Bad/incomplete input data Failed convert data from base64 to bytes         |
|ConvertImageToJPGError                  |18002     |Bad/incomplete input data Failed convert bytes to jpg                      |
|SavingImageErrorLocal                   |19001     |Internal server error Failed to save image in store                        |
|DeleteImageErrorLocal                   |19002     |Internal server error Failed to remove image from store                    |
|DeleteImagesErrorLocal                  |19003     |Internal server error Failed to remove image from store                    |
|CreateBucketErrorLocal                  |19004     |Internal server error Failed to create bucket                              |
|GettingBucketsErrorLocal                |19005     |Internal server error Failed to get bucket list                            |
|GettingImageErrorLocal                  |19006     |Internal server error Failed to get image from store                       |
|SavingObjectErrorLocal                  |19007     |Internal server error Failed to save object in store                       |
|DeleteObjectErrorLocal                  |19008     |Internal server error Failed to remove object from store                   |
|DeleteObjectsErrorLocal                 |19009     |Internal server error Failed to remove objects from store                  |
|GettingObjectErrorLocal                 |19010     |Internal server error Failed to get object from store                      |
|GettingObjectsErrorLocal                |19011     |Internal server error Failed to get objects from store                     |
|DeleteBucketErrorLocal                  |19012     |Internal server error Failed to delete bucket                              |
|SavingImageErrorS3                      |20001     |Internal server error Failed to save image in store                        |
|DeleteImageErrorS3                      |20002     |Internal server error Failed to remove image from store                    |
|DeleteImagesErrorS3                     |20003     |Internal server error Failed to remove image from store                    |
|CreateBucketErrorS3                     |20004     |Internal server error Failed to create bucket                              |
|RequestS3Error                          |20005     |Internal server error Request to S3 Failed                                 |
|RequestS3Forbidden                      |20006     |Internal server error Request to S3 Forbidden                              |
|RequestTimeoutToS3Error                 |20007     |Internal server error                                                      |
|S3ConnectionRefusedError                |20008     |Internal server error S3 Connection Refused                                |
|ConnectTimeoutToS3Error                 |20009     |Internal server error                                                      |
|S3UnknownError                          |20010     |Internal server error Unknown s3 error                                     |
|GettingBucketsErrorS3                   |20011     |Internal server error Failed to get bucket list                            |
|GettingImageErrorS3                     |20012     |Internal server error Failed to get image from store                       |
|SavingObjectErrorS3                     |20013     |Internal server error Failed to save object in store                       |
|DeleteObjectErrorS3                     |20014     |Internal server error Failed to remove object from store                   |
|DeleteObjectsErrorS3                    |20015     |Internal server error Failed to remove object list from store              |
|GettingObjectErrorS3                    |20016     |Internal server error Failed to get object from store                      |
|GettingObjectsErrorS3                   |20017     |Internal server error Failed to get object list from store                 |
|DeleteBucketsErrorS3                    |20018     |Internal server error Failed to delete bucket                              |
|FaceWithAttributeOrIdAlreadyExist       |22001     |Unique constraint error                                                    |
|FaceNotFound                            |22002     |Object not found Face not found                                            |
|ListNotFound                            |22003     |Object not found List not found                                            |
|FacesNotFound                           |22004     |Object not found One or more faces not found                               |
|ListsNotFound                           |22005     |Object not found One or more lists not found                               |
|PersonsNotFound                         |22006     |Object not found One or more persons not found                             |
|PersonNotFound                          |22007     |Object not found Person not found                                          |
|FaceAlreadyAttach                       |22008     |Unique constraint error This face is already attached to the person        |
|EventNotFound                           |23001     |Object not found Event not found                                           |
|EventsNotFound                          |23002     |Object not found One or more events not found                              |
|AerospikeClientError                    |24001     |Internal server error Mis-configuration or misuse of the API methods       |
|AerospikeServerError                    |24002     |Internal server error Error returned from the cluster                      |
|AerospikeUnknownError                   |24003     |Internal server error Unknown aerospike error                              |
|AttributesForUpdateNotFound             |25001     |Object not found Attributes for update not found                           |
|AttributesNotFound                      |25002     |Object not found Attributes not found                                      |
|FailDecodeDescriptor                    |25003     |Bad/incomplete input data Failed to decode descriptor from base64          |
|FailEncodeDescriptor                    |25004     |Bad/incomplete input data Failed to encode descriptor to base64            |
|IndexTaskNotFound                       |26001     |Object not found Index task not found                                      |
|GenerationNotFound                      |26002     |Internal server error Generation not found in indexer                      |
|UnknownStatusOfIndexer                  |26003     |Internal server error Not expected status of indexer                       |
|FailedUploadIndex                       |26004     |Internal server error                                                      |
|FailedReloadIndex                       |26005     |Internal server error                                                      |
|BadStatusOfUploadTask                   |26007     |Internal server error                                                      |
|BadStatusOfRestartTask                  |26008     |Internal server error                                                      |
|ListNotSatisfyIndexationCondition       |26009     |Bad/incomplete input data                                                  |
|SettingNotFound                         |27001     |Object not found Setting not found                                         |
|SettingIntegrityError                   |27002     |Integrity error                                                            |
|FailedCheckConnectionToService          |27003     |Bad/incomplete input data                                                  |
