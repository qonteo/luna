import uuid
from uuid import UUID

from sqlalchemy import create_engine, and_, func
from sqlalchemy import update, insert, delete
from sqlalchemy.orm import Query
from typing import List
from typing import TypeVar
from db import models
from db.models import Account
from crutches_on_wheels.utils.timer import timer
from configs.config import SQLALCHEMY_DATABASE_URI, DB
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from functools import wraps
from passlib.hash import pbkdf2_sha256

uuidStr = TypeVar('uuidStr', str, UUID)  #: uuid4 or uuid4 converted into string

pool = None  #: poll of connections to postgres, created by every worker at the moment of first connection
literal_binds = False
if DB == 'postgres':
    engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"connect_timeout": 5})
else:
    # analogue of connect_timeout for oracle not found or not exists
    engine = create_engine(SQLALCHEMY_DATABASE_URI)


def exceptionWrap(wrapFunc):
    """
    Decorator for catching exceptions when composing queries to the database.

    :return: If exception is not caught, will be raise VLException(Error.CreateQueryError), reraise VLException
    """

    @wraps(wrapFunc)
    def wrap(*func_args, **func_kwargs):
        try:
            return wrapFunc(*func_args, **func_kwargs)
        except VLException:
            raise
        except Exception:
            func_args[0].logger.exception()
            raise VLException(Error.CreateQueryError)

    return wrap


class DBContext:
    """
    Class for requests to postgres.
    """

    def __init__(self, logger):
        self.logger = logger

    @exceptionWrap
    def checkoutLoginPassword(self, login: str, password: str) -> str:
        """
        Check of login/password pair existence.

        Args:
            login:  login for authentication
            password: password for authentication
        Returns:
            account id
        Raises:
            VLException(Error.AccountNotFound, 401, isCriticalError = False),
            VLException(Error.AccountNotFound, 401, isCriticalError = False)
        """
        with engine.begin() as connection:
            query = Query([models.Account.account_id, models.Account.password])
            query = query.filter(and_(models.Account.email == login))
            acc = connection.execute(query.statement).cursor.fetchone()

            if acc is None:
                raise VLException(Error.AccountNotFound, 401, isCriticalError=False)
            accId = acc[0]
            pwdHash = acc[1]
            if not pbkdf2_sha256.verify(password, pwdHash):
                raise VLException(Error.AccountNotFound, 401, isCriticalError=False)
            return accId

    @exceptionWrap
    def checkAccountIsActive(self, accountId: uuidStr) -> bool:
        """
        Check if account is active or not.

        Args:
            accountId: id of account on check.
        Returns:
            true if account is active, else false
        Raises:
            VLException(Error.AccountNotFound)
        """
        with engine.begin() as connection:
            query = Query(models.Account.active)
            query = query.filter(models.Account.account_id == accountId)
            state = connection.execute(query.statement).cursor.fetchone()

            if state is None or state[0] is None:
                raise VLException(Error.AccountNotFound)
            return state[0]

    @exceptionWrap
    def createAccountToken(self, accountId: uuidStr, info="") -> str:
        """
        Creation of token for the account.

        Args:
            info: user info for token
            accountId: account id, the token is created to.
        Returns:
            token_id
        """
        with engine.begin() as connection:
            token_id = str(uuid.uuid4())
            st = insert(models.AccountToken).values(account_id=accountId, token_id=token_id,
                                                    token_info=info)
            connection.execute(st)

            return token_id

    @exceptionWrap
    def updateTokenInfo(self, tokenId: uuidStr, accountId: uuidStr, data: str) -> None:
        """
        Update of token information.

        Args:
            tokenId: token id, which is updated
            accountId: account id, token is linked to.
            data: new token data
        """
        with engine.begin() as connection:
            st = update(models.AccountToken).where(models.AccountToken.account_id == accountId).where(
                models.AccountToken.token_id == tokenId).values(token_info=data)
            connection.execute(st)

    @exceptionWrap
    def checkTokenExist(self, tokenId: uuidStr, accountId: uuidStr) -> bool:
        """
        Check if token with id is linked to account.

        Args:
            tokenId:  token id.
            accountId: account id.
        Returns:
            True if token is exist else False
        """
        with engine.begin() as connection:
            query = Query(models.AccountToken.token_id)
            query = query.filter(and_(models.AccountToken.token_id == tokenId,
                                                models.AccountToken.account_id == accountId))
            count = len(connection.execute(query.statement).cursor.fetchall())
            return True if count == 1 else False

    @exceptionWrap
    def getTokenById(self, tokenId: uuidStr, accountId: uuidStr) -> str:
        """
        Get token_info by  id token and account token_info.

        Args:
            tokenId: id  token
            accountId: account id, token is linked to.
        Returns:
            token data
        Raises:
            VLException(Error.TokenNotFound, 404)
        """
        with engine.begin() as connection:
            query = Query(models.AccountToken.token_info)
            query = query.filter(and_(models.AccountToken.token_id == tokenId,
                                  models.AccountToken.account_id == accountId))
            res = connection.execute(query.statement).cursor.fetchone()
            if res is None or res[0] is None:
                raise VLException(Error.TokenNotFound, 404, isCriticalError=False)
            return res[0]

    @exceptionWrap
    def getAccountByAccountId(self, accountId: uuidStr) -> Account:
        """
        Receive account by id.

        Args:
            accountId: account id
        Returns:
            account (tuple with account_id, status, email, password, organization_name)
        """
        with engine.begin() as connection:
            query = Query(models.Account)
            query = query.filter(and_(models.Account.account_id == accountId))
            value = connection.execute(query.statement).cursor.fetchone()
            acc = models.Account().fillAccount(value)
            return acc

    @exceptionWrap
    def getAccountTokens(self, accountId: uuidStr, page=1, pageSize=100) -> list:
        """
        Receive account token list

        Args:
            accountId: account id
            page: page
            pageSize: page size
        Returns:
            list of token
        """
        with engine.begin() as connection:
            query = Query([models.AccountToken.token_id, models.AccountToken.token_info])
            query = query.filter(models.AccountToken.account_id == accountId).order_by(
                models.AccountToken.token_id.asc()).offset((page - 1) * pageSize).limit(pageSize)
            res = connection.execute(query.statement).cursor.fetchall()
            return res

    @exceptionWrap
    def getAccountTokenCount(self, accountId: uuidStr) -> int:
        """
        Get account tokens count

        Args:
            accountId: account id
        Returns:
            count of account tokens
        """
        with engine.begin() as connection:
            query = Query([func.count(models.AccountToken.token_id).label('count')])
            query = query.filter(models.AccountToken.account_id == accountId)
            res = connection.execute(query.statement).cursor.fetchone()[0]
            return res

    @exceptionWrap
    def registerAccount(self, name: str, email: str, password: str) -> tuple:
        """
        Account creation. Account and first token are created simultaneously.

        Args:
            name: organization name
            email: e-mail
            password: password
        Returns:
            tuple with account id and token id
        Raises:
            VLException(Error.EmailExist, 409, isCriticalError = False)
        """
        with engine.begin() as connection:
            query = Query(models.Account.email)
            query = query.filter(models.Account.email == email)
            countRes = len(connection.execute(query.statement).cursor.fetchall())
            if countRes == 0:
                accountId = str(uuid.uuid4())
                pwdHash = pbkdf2_sha256.hash(password)
                createAccountSt = insert(models.Account).values(account_id=accountId, organization_name=name,
                                                                email=email, active=True, password=pwdHash)
                connection.execute(createAccountSt)

                tokenId = str(uuid.uuid4())
                createTokenSt = insert(models.AccountToken).values(account_id=accountId, token_id=tokenId,
                                                                   token_info="first token")
                connection.execute(createTokenSt)
                return accountId, tokenId
            else:
                raise VLException(Error.EmailExist, 409, isCriticalError=False)

    @exceptionWrap
    def removeTokens(self, tokens: List[uuidStr], accountId: uuidStr) -> None:
        """
        Delete list of account.

        Args:
            tokens:  list of tokens
            accountId: account id. tokens are linked to
        """
        with engine.begin() as connection:
            st = delete(models.AccountToken).where(and_(models.AccountToken.token_id.in_(tokens),
                                                        models.AccountToken.account_id == accountId))
            connection.execute(st)

    @exceptionWrap
    def getAccountIdByToken(self, tokenId: uuidStr) -> str:
        """
        Receive account id by token.

        Args:
            tokenId: token id
        Returns:
            account id
        Raises:
            VLException(Error.AccountNotFound, isCriticalError = False)
        """
        with engine.begin() as connection:
            query = Query(models.AccountToken.account_id)
            query = query.filter(models.AccountToken.token_id == tokenId)
            accId = connection.execute(query.statement).cursor.fetchone()
            if accId is None or accId[0] is None:
                raise VLException(Error.AccountNotFound, isCriticalError=False)
            else:
                return accId[0]
