import base64

from crutches_on_wheels.handlers.query_getters import isUUID4
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException


def getAuthByStr(authStr, dbContext):
    """
    Get authorization data with following account check.
    
    :param dbContext: context for connecting to db
    :param authStr: string with basic auth
    :return: result of db_function.checkoutLoginPassword
    """

    authBase64 = authStr[len("Basic "):]
    try:
        authData = base64.b64decode(authBase64).decode("utf-8")
        towDotIndex = authData.index(":")
        login = authData[0:towDotIndex]
        password = authData[towDotIndex + 1:]
    except Exception as e:
        raise VLException(Error.BadHeaderAuth, 400, exception = e, isCriticalError = False)
    accIdRes = dbContext.checkoutLoginPassword(login.lower(), password)
    return accIdRes


def basicAuth(authStr, dbContext):
    """
    Function for basic authorization.

    :param dbContext: context for connecting to db
    :param authStr: string with authentication (cookie or header)
    :rtype: str
    :return: account id
    """
    if not authStr:
        raise VLException(Error.BadHeaderAuth, 400)
    if not (authStr.startswith("Basic") or authStr.startswith("basic")):
        raise VLException(Error.BadHeaderAuth, 400)

    return getAuthByStr(authStr, dbContext)


def tokenAuth(tokenId, dbContext) -> str:
    """
    Function for authorization by token.

    :param dbContext: context for connecting to db
    :param tokenId: token id from header
    :rtype: str
    :return: If all authorization data is correct, system returns *Result* with account_id

            If data is incorrect, error description is returned
    """
    if not tokenId:
        raise VLException(Error.BadHeaderAuth, 400)
    else:
        formatCheckRes = isUUID4(tokenId)
        if formatCheckRes:
            accountId = dbContext.getAccountIdByToken(tokenId)
            return accountId
        else:
            raise VLException(Error.BadFormatUUID, 400)


def accountIsActive(accountId: str, dbContext) -> bool:
    """
    Check whether account is active or not.
    :param dbContext: context for connecting to db
    :param accountId: account id
    :rtype: bool
    :return: state of account
    """
    accActive = dbContext.checkAccountIsActive(accountId)
    return accActive
