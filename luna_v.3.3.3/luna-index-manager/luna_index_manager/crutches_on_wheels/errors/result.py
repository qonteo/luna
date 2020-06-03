"""
Optional
"""
from .errors import ErrorInfo, Error


class Result:
    """
    Optional
    Attributes:
        error: error or Error.Success
        value: value
    """
    def __init__(self, error: ErrorInfo, value: object):
        self.error = error
        self.value = value

    def getStatus(self) -> bool:
        """
        Get status of optional
        Returns:
            true is error is equal to Error.Success otherwise False
        """
        return self.error == Error.Success

    @property
    def success(self) -> bool:
        """
        Property for checking status is success or not.

        Returns:
             self.getStatus()
        """
        return self.getStatus()

    @property
    def fail(self) -> bool:
        """
        Property for checking status is failed or not.

        Returns:
             not self.getStatus()
        """
        return not self.getStatus()

    @property
    def errorCode(self) -> int:
        return self.error.errorCode

    def getError(self) -> ErrorInfo:
        """
        Get error of optional.

        Returns:
            self.error
        """
        return self.error

    @property
    def description(self) -> str:
        """
        Get error description

        Returns:
            self.error.description
        """
        return self.error.description
