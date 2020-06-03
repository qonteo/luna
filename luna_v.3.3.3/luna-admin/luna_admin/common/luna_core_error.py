"""
Module for generation error from responses.
"""
from luna3.common.luna_response import LunaResponse
from crutches_on_wheels.utils.log import Logger
from crutches_on_wheels.errors.errors import ErrorInfo


def generateLunaCoreRequestError(response: LunaResponse, logger: Logger) -> ErrorInfo:
    """
    Generate error from LunaResponse

    Args:
        response: response from luna3 function
        logger: logger

    Returns:
        ErrorInfo with description and error code from response json.
    """
    error = ErrorInfo(response.json["error"] if "error" in response.json else response.json["error_code"], response.json["detail"])

    logger.error("LUNA Core request failed, detail:{}, error code: {}".format(error.description,
                                                                              error.errorCode))
    return error
