# -*- coding: utf-8 -*-
"""
Module realize a list of errors
"""
import inspect


class ErrorInfo:
    """
    VL error.

    Attributes:
        errorCode: error code
        description: short error description
        detail: full error description
    """
    __slots__ = ['errorCode', 'description', 'detail']

    def __init__(self, code: int, description: str, detail: str):
        self.description = description
        self.errorCode = code
        self.detail = detail

    def __eq__(self, other):
        return self.errorCode == other.errorCode


class LunaCoreError:
    """
     Structure to save errors in LUNA Core.
    """
    BadConfig = ErrorInfo(100, 'Bad/incomplete configuration', "{}")
    BadQuery = ErrorInfo(101, 'Bad/incomplete query', "{}")
    BadBody = ErrorInfo(102, 'Bad/incomplete body', "{}")
    OutOfMemoryError = ErrorInfo(104, 'Out of memory', "{}")
    GenericError = ErrorInfo(200, 'Generic error', "{}")
    # data base
    PutRecord = ErrorInfo(1000, 'Failed to put DB record', "{}")
    GetRecord = ErrorInfo(1001, 'Failed to get DB record', "{}")
    TouchRecord = ErrorInfo(1002, 'Failed to touch DB record', "{}")
    DelRecord = ErrorInfo(1003, 'Failed to delete DB record', "{}")
    AppendRecord = ErrorInfo(1004, 'Failed to append to DB record', "{}")
    SerializeObject = ErrorInfo(1008, 'Failed to serialize object', "{}")
    DeserializeObject = ErrorInfo(1009, 'Failed to deserialize object', "{}")
    OutOfMemory = ErrorInfo(1010, 'Out of memory', "{}")
    # message subsystem
    BadMessage = ErrorInfo(2000, 'Bad/incomplete message package', "{}")
    CoreBadContentType = ErrorInfo(2001, 'Bad/unsupported message content type', "{}")
    WorkerCallFailed = ErrorInfo(2002, 'Failed to call a remote worker', "{}")
    # image processing
    CreateImage = ErrorInfo(3000, 'Failed to create image', "{}")
    DecodeImage = ErrorInfo(3001, 'Failed to decode image data', "{}")
    ImageSize = ErrorInfo(3002, 'Incorrect image size', "{}")
    # extractor
    CreateObject = ErrorInfo(4000, 'Failed to create FSDK object', "{}")
    DetectFeatureSet = ErrorInfo(4001, 'Failed to detect a feature set', "{}")
    DetectFace = ErrorInfo(4002, 'Failed to detect a face', "{}")
    NoFaces = ErrorInfo(4003, 'No faces found', "{}")
    MultipleFaces = ErrorInfo(4004, 'Multiple faces found', "{}")
    BadInput = ErrorInfo(4005, 'Bad/incomplete input data', "{}")
    ConvertImage = ErrorInfo(4007, 'Failed to convert image format', "{}")
    EstimateAttributes = ErrorInfo(4009, 'Failed to estimate face image attributes', "{}")
    DescriptorQuality = ErrorInfo(4010, 'Descriptor quality is too low', "{}")
    ExtractDescriptor = ErrorInfo(4011, 'Failed to extract a descriptor', "{}")
    # descriptor match
    MatchCreateObject = ErrorInfo(5001, 'Failed to create FSDK object', "{}")
    MatchAppendToBatch = ErrorInfo(5002, 'Failed to add descriptor to batch', "{}")
    MatchDescriptors = ErrorInfo(5003, 'Failed to match descriptors', "{}")
    MatchBadInput = ErrorInfo(5004, 'Bad/incomplete input data', "{}")
    # descriptors' lists
    ListBadInput = ErrorInfo(6000, 'Bad/incomplete input data', "{}")
    ListBadMode = ErrorInfo(6001, 'Unknown operation mode', "{}")
    LunaServerError = ErrorInfo(7004, 'Internal server error', "{}")

    LunaCoreConnectionTimeout = ErrorInfo(9001, 'Network error', 'Connection timeout to LUNA Core')
    LunaCoreRequestTimeout = ErrorInfo(9002, 'Network error', 'Request timeout to Luna Core')
    LunaCoreRequestError = ErrorInfo(9003, 'Unknown error', '{} request failed.  error_code: {}, detail: {}')


class DataBaseError:
    """
    Database errors
    """
    GetConnectionToDBError = ErrorInfo(10001, 'Database error', 'Connection to database is refused')
    CreateQueryError = ErrorInfo(10002, 'Database error', 'Creating sql request failed')
    ConnectionClosed = ErrorInfo(10013, 'Database error', 'Connection to database is closed')
    ExecuteError = ErrorInfo(10015, 'SQL error', 'Execute sql request failed')


class LunaApiError:
    """
    Luna Api errors
    """
    AccountNotFound = ErrorInfo(11002, 'Authorization failed', 'Account corresponding login/password not found')
    AccountIsNotActive = ErrorInfo(11004, 'Account is suspended', 'Account is suspended')
    MatchingResultEmpty = ErrorInfo(11007, 'Matching errors', 'Empty matching result')
    NoPhotoToMatching = ErrorInfo(11008, 'Matching errors', 'No descriptors for matching')
    RequestInternalServerError = ErrorInfo(11009, 'Internal server error', 'Internal server error')
    EmailExist = ErrorInfo(11011, 'Unique constraint error', 'An account with given email already exists')
    ManyFaces = ErrorInfo(11012, 'Extract policy error', "Too many faces found")
    IncorrectEmail = ErrorInfo(11013, 'Bad/incomplete input data', 'Invalid email address')
    PasswordBadLength = ErrorInfo(11014, 'Bad/incomplete input data',
                                  'Length password  must be between 8 and 32 symbols')
    BigUserData = ErrorInfo(11015, 'Bad/incomplete input data', "Max length user data is 128 symbols")
    LinkDescriptorAlreadyExist = ErrorInfo(11016, 'Unique constraint error',
                                           "This descriptor is already attached to the person or list")
    DescriptorNotFound = ErrorInfo(11018, "Object not found", 'Descriptor not found')
    AccountListNotFound = ErrorInfo(11019, "Object not found", 'Account list not found')
    ObjectNotFound = ErrorInfo(11020, "Object not found", "One or more {} not found")
    TokenNotFound = ErrorInfo(11022, "Object not found", 'Token not found')
    PortraitNotFound = ErrorInfo(11024, "Object not found", 'Portrait not found')
    UnknownErrorFromLunaFaces = ErrorInfo(11025, 'Internal server error', 'Unknown error from luna faces')


class RESTAPIError:
    """
    Rest api common errors
    """
    BadFormatUUID = ErrorInfo(12001, 'Bad/incomplete input data',
                              'Object in  query is not UUID4, format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx')
    RequestNotContainsJson = ErrorInfo(12002, 'Bad/incomplete input data', 'Request does not contain json')
    FieldNotInJSON = ErrorInfo(12003, 'Bad/incomplete input data', "Field '{}' not found in json")
    BadTypeOfFieldInJSON = ErrorInfo(12004, 'Bad/incomplete input data', "Field '{}' must be {}")
    EmptyJson = ErrorInfo(12005, 'Bad/incomplete input data', 'Request contain empty json')
    EmptyField = ErrorInfo(12009, 'Bad/incomplete input data', "Empty field '{}'")
    BadHeaderAuth = ErrorInfo(12010, 'Bad/incomplete input data',
                              'This resource need "Authorization" authorization headers')
    BadQueryParams = ErrorInfo(12012, 'Bad/incomplete input data', "Bad query parameters '{}'")
    PageNotFoundError = ErrorInfo(12013, "Resource not found", "Page not found")
    QueryParameterNotFound = ErrorInfo(12014, 'Bad/incomplete input data', "Required parameters '{}' not found")
    RequiredQueryParameterNotFound = ErrorInfo(12016, 'Bad/incomplete input data', "No one  parameters '{}' not found")
    BadContentType = ErrorInfo(12017, 'Bad/incomplete input data', "Bad content type")
    UnsupportedQueryParm = ErrorInfo(12018, 'Bad/incomplete input data', "Unsupported param '{}'")
    BadAuthParam = ErrorInfo(12019, 'Bad/incomplete input data', "Bad format of authorization header")
    AuthFailedError = ErrorInfo(12020, 'Bad/incomplete input data', "Unknown error authorization")
    MethodNotAllowed = ErrorInfo(12021, "Method not allowed", "Method not allowed")
    BadInputJson = ErrorInfo(12022, 'Bad/incomplete input data',
                             "Failed to validate input json. Path: '{}',  message: '{}'")
    NotAcceptable = ErrorInfo(12023, 'Bad/incomplete input data', "Not Acceptable")
    UnsupportedMediaType = ErrorInfo(12024, 'Bad/incomplete input data', "Unsopported media type")
    SpecifiedTypeNotMatchDataType = ErrorInfo(12025, 'Bad/incomplete input data',
                                              "Specified content type does not match data type")
    BadInputXPK = ErrorInfo(12026, 'Bad/incomplete input data', "Failed to parse XPK")


class LunaImageStoreError:
    """
    Luna-image-store errors
    """
    RequestLunaImageStoreError = ErrorInfo(13002, 'Internal server error', 'Request to luna-image-store failed')
    ImageNotFoundError = ErrorInfo(13003, "Object not found", 'Image not found')
    ImageCountExceededLimit = ErrorInfo(13004, 'Bad/incomplete input data', 'Image count exceeded limit 1000')
    BucketNotFound = ErrorInfo(13005, "Object not found", 'Bucket not found')
    BucketAlreadyExist = ErrorInfo(13006, 'Unique constraint error', 'Bucket already exist')
    ObjectInBucketNotFound = ErrorInfo(13007, "Object not found", 'Object not found')
    ObjectInBucketAlreadyExist = ErrorInfo(13008, 'Unique constraint error', 'Object already exist')
    ObjectInBucketCountExceededLimit = ErrorInfo(13009, 'Bad/incomplete input data', 'Object count exceeded limit 1000')


class PluginsError:
    """
    Plug-ins errors
    """
    ErrorGetPortraitPlugin = ErrorInfo(14001, "Plugin error", 'Failed get portrait from plugin')
    ErrorSavePortraitPlugin = ErrorInfo(14002, "Plugin error", 'Failed save portrait to plugin')


class LunaAdmin:
    """
    Luna-admin errors
    """
    ReExtractExceedMaximumIteration = ErrorInfo(16008, 'Internal server error', "Exceed maximum iteration count")
    TaskNotFound = ErrorInfo(16009, "Object not found", "Task not found")
    RequestToTaskServerTornadoError = ErrorInfo(16010, 'Internal server error', "Request to task server failed")
    CheckConnectionToReExtractBroker = ErrorInfo(16011, 'Internal server error',
                                                 "Connection  check to re-extract broker is failed")


class InfluxError:
    InfluxConnectionTimeout = ErrorInfo(17001, 'Internal server error', "Connection timeout to influxdb")


class ImageProcessingError:
    ConvertBase64Error = ErrorInfo(18001, 'Bad/incomplete input data', "Failed convert data from base64 to bytes")
    ConvertImageToJPGError = ErrorInfo(18002, 'Bad/incomplete input data', "Failed convert bytes to jpg")


class LocalStoreError:
    SavingImageErrorLocal = ErrorInfo(19001, 'Internal server error', 'Failed to save image in store')
    DeleteImageErrorLocal = ErrorInfo(19002, 'Internal server error', 'Failed to remove image from store')
    DeleteImagesErrorLocal = ErrorInfo(19003, 'Internal server error', 'Failed to remove image from store')
    CreateBucketErrorLocal = ErrorInfo(19004, 'Internal server error', 'Failed to create bucket')
    GettingBucketsErrorLocal = ErrorInfo(19005, 'Internal server error', "Failed to get  bucket list")
    GettingImageErrorLocal = ErrorInfo(19006, 'Internal server error', 'Failed to get image from store')
    SavingObjectErrorLocal = ErrorInfo(19007, 'Internal server error', 'Failed to save object in store')
    DeleteObjectErrorLocal = ErrorInfo(19008, 'Internal server error', 'Failed to remove object from store')
    DeleteObjectsErrorLocal = ErrorInfo(19009, 'Internal server error', 'Failed to remove objects from store')
    GettingObjectErrorLocal = ErrorInfo(19010, 'Internal server error', 'Failed to get object from store')
    GettingObjectsErrorLocal = ErrorInfo(19011, 'Internal server error', 'Failed to get objects from store')
    DeleteBucketErrorLocal = ErrorInfo(19012, 'Internal server error', 'Failed to delete bucket')


class S3StorageError:
    """
    S3 errors
    """

    SavingImageErrorS3 = ErrorInfo(20001, 'Internal server error', 'Failed to save image in store')
    DeleteImageErrorS3 = ErrorInfo(20002, 'Internal server error', 'Failed to remove image from store')
    DeleteImagesErrorS3 = ErrorInfo(20003, 'Internal server error', 'Failed to remove image from store')
    CreateBucketErrorS3 = ErrorInfo(20004, 'Internal server error', 'Failed to create bucket')
    RequestS3Error = ErrorInfo(20005, 'Internal server error', 'Request to S3 Failed')
    RequestS3Forbidden = ErrorInfo(20006, 'Internal server error', 'Request to S3 Forbidden')
    RequestTimeoutToS3Error = ErrorInfo(20007, 'Internal server error',
                                        'Request time to S3 is longer than the established time')
    S3ConnectionRefusedError = ErrorInfo(20008, 'Internal server error', 'S3 Connection Refused')
    ConnectTimeoutToS3Error = ErrorInfo(20009, 'Internal server error',
                                        'Connect time to S3 is longer than the established time')

    S3UnknownError = ErrorInfo(20010, 'Internal server error', 'Unknown s3 error')
    GettingBucketsErrorS3 = ErrorInfo(20011, 'Internal server error', "Failed to get bucket list")
    GettingImageErrorS3 = ErrorInfo(20012, 'Internal server error', 'Failed to get image from store')

    SavingObjectErrorS3 = ErrorInfo(20013, 'Internal server error', 'Failed to save object in store')
    DeleteObjectErrorS3 = ErrorInfo(20014, 'Internal server error', 'Failed to remove object from store')
    DeleteObjectsErrorS3 = ErrorInfo(20015, 'Internal server error', 'Failed to remove object list from store')
    GettingObjectErrorS3 = ErrorInfo(20016, 'Internal server error', 'Failed to get object from store')
    GettingObjectsErrorS3 = ErrorInfo(20017, 'Internal server error', 'Failed to get object list from store')

    DeleteBucketsErrorS3 = ErrorInfo(20018, 'Internal server error', "Failed to delete bucket")


class LunaFaces:
    """
    Luna-faces error
    """
    FaceWithAttributeOrIdAlreadyExist = ErrorInfo(22001, 'Unique constraint error',
                                                  'Face with the same attribute_id or face id already exist')
    FaceNotFound = ErrorInfo(22002, "Object not found", 'Face not found')
    ListNotFound = ErrorInfo(22003, "Object not found", 'List not found')
    FacesNotFound = ErrorInfo(22004, "Object not found", 'One or more faces not found')
    ListsNotFound = ErrorInfo(22005, "Object not found", 'One or more lists not found')
    PersonsNotFound = ErrorInfo(22006, "Object not found", 'One or more persons not found')
    PersonNotFound = ErrorInfo(22007, "Object not found", 'Person not found')
    FaceAlreadyAttach = ErrorInfo(22008, 'Unique constraint error', 'This face is already attached to the person')


class LunaEvents:
    """
    Luna-events error
    """
    EventNotFound = ErrorInfo(23001, "Object not found", 'Event not found')
    EventsNotFound = ErrorInfo(23002, "Object not found", 'One or more events not found')


class AerospikeError:
    """
    Aerospike errors
    """
    AerospikeClientError = ErrorInfo(24001, 'Internal server error', 'Mis-configuration or misuse of the API methods')
    AerospikeServerError = ErrorInfo(24002, 'Internal server error', 'Error returned from the cluster')
    AerospikeUnknownError = ErrorInfo(24003, 'Internal server error', 'Unknown aerospike error')


class LunaAttributes:
    """
    Luna-attributes errors
    """
    AttributesForUpdateNotFound = ErrorInfo(25001, "Object not found", 'Attributes for update not found')
    AttributesNotFound = ErrorInfo(25002, "Object not found", 'Attributes not found')
    FailDecodeDescriptor = ErrorInfo(25003, 'Bad/incomplete input data', 'Failed to decode descriptor from base64')
    FailEncodeDescriptor = ErrorInfo(25004, 'Bad/incomplete input data', 'Failed to encode descriptor to base64')


class IndexManagerError:
    """
    Index manager errors
    """
    IndexTaskNotFound = ErrorInfo(26001, "Object not found", 'Index task not found')
    GenerationNotFound = ErrorInfo(26002, 'Internal server error', 'Generation not found in indexer')
    UnknownStatusOfIndexer = ErrorInfo(26003, 'Internal server error', "Not expected status of indexer")
    FailedUploadIndex = ErrorInfo(26004, 'Internal server error',
                                  "Failed start upload generation {} on daemon {}, reason: {}")
    FailedReloadIndex = ErrorInfo(26005, 'Internal server error',
                                  "Failed start reload generation {} on daemon {}, reason: {}")
    BadStatusOfUploadTask = ErrorInfo(26007, 'Internal server error',
                                      "Not expected status of upload task. Status: {}, daemon: {}, generation: {}")
    BadStatusOfRestartTask = ErrorInfo(26008, 'Internal server error',
                                       "Not expected status of restart task. Status: {}, daemon: {}, generation: {}")
    ListNotSatisfyIndexationCondition = ErrorInfo(26009, 'Bad/incomplete input data',
                                                  "List does not satisfy to the indexation condition")


class ConfiguratorError:
    """
    Luna-configurator errors.
    """
    SettingNotFound = ErrorInfo(27001, "Object not found", 'Setting not found')
    SettingIntegrityError = ErrorInfo(27002, 'Integrity error',
                                      "Setting with the following fields already exists: name: {} priority: {}")
    FailedCheckConnectionToService = ErrorInfo(27003, 'Bad/incomplete input data',
                                                 "Connection  check to service is failed")


class Error(LunaCoreError, DataBaseError, LunaApiError, RESTAPIError, LunaImageStoreError, PluginsError, InfluxError,
            S3StorageError, LocalStoreError, ImageProcessingError, LunaAdmin, LunaFaces, LunaEvents, AerospikeError,
            LunaAttributes, IndexManagerError, ConfiguratorError):
    """
    Common errors class.
    """

    Success = ErrorInfo(0, 'Success', 'Success')
    UnknownError = ErrorInfo(1, 'Internal server error', 'Unknown error')

    @staticmethod
    def getErrorByErrorCode(errorCode: int) -> ErrorInfo:
        """
        Find error by error code

        Args:
            errorCode: error code

        Returns:
             Error.UnknownError if error not found.
        """
        members = inspect.getmembers(Error)
        for member in members:
            if type(member[1]).__name__ == "ErrorInfo":
                if member[1].errorCode == errorCode:
                    return getattr(Error, member[0])
        return Error.UnknownError

    @staticmethod
    def generateError(error: ErrorInfo, msg: str) -> ErrorInfo:
        """
        Generate error with custom details

        Args:
            error: error
            msg: new details

        Returns:
            ErrorInfo(error.errorCode, error.description, msg)

        """
        return ErrorInfo(error.errorCode, error.description, msg)

    @staticmethod
    def formatError(error: ErrorInfo, *formatArgs) -> ErrorInfo:
        """
        Format error detail

        Args:
            error: errors
            *formatArgs:  args for formatting

        Returns:
            formatted error
        """
        return ErrorInfo(error.errorCode, error.description, error.detail.format(*formatArgs))
