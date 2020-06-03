"""
Module for work with api database
"""
from typing import List, Tuple, Union, Optional
from sqlalchemy import and_, Column
from sqlalchemy import update, func
from sqlalchemy.orm import Query
from sqlalchemy.sql.elements import BinaryExpression
from app.api_db import models, engine
from functools import wraps
from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException


def exceptionWrap(wrapFunc):
    """
    Decorator for catching exceptions when composing queries to the database.

    Args:
        wrapFunc: function

    Returns:
        If exception is not caught, function result is returned, else Result\
        with value of exception is returned
    """

    @wraps(wrapFunc)
    def wrap(*func_args, **func_kwargs):
        try:
            return wrapFunc(*func_args, **func_kwargs)
        except VLException:
            raise
        except Exception as e:
            func_args[0].logger.exception()
            raise VLException(Error.ExecuteError)

    return wrap


class DBContext:
    """
    DB context

    Attributes:
        logger: request logger
    """

    def __init__(self, logger):
        self.logger = logger

    @exceptionWrap
    def getAllAccounts(self) -> List[str]:
        """
        Get all accounts ids

        Returns:
            list of account id
        """
        with engine.begin() as connection:
            query = Query(models.Account.account_id)
            accountsId = connection.execute(query.statement).fetchall()
            accountsId = [accountId[0] for accountId in accountsId]
            return accountsId

    @exceptionWrap
    def blockAccount(self, accountId: str, state: bool) -> None:
        """
        Block or unblock account.

        Args:
            accountId: account id
            state: true - account is active, false - is suspended
        """
        with engine.begin() as connection:
            st = update(models.Account).where(models.Account.account_id == accountId).values(active=state)
            connection.execute(st)

    @exceptionWrap
    def getAccounts(self, page: int = 1, pageSize: int = 10) -> List[Tuple[str, str, str, bool]]:
        """
        Get accounts with pagination
        Args:
            page:
            pageSize:

        Returns:
            list of tuples (account_id, organization_name, email, active)
        """
        with engine.begin() as connection:
            query = Query([models.Account.account_id, models.Account.organization_name, models.Account.email,
                           models.Account.active])
            query = query.filter().order_by(models.Account.email).offset((page - 1) * pageSize).limit(pageSize)

            accounts = connection.execute(query.statement).fetchall()
            return [(account[0], account[1], account[2], account[3]) for account in accounts]

    @exceptionWrap
    def getAccount(self, accountId: str) -> Union[Tuple[str, str, bool], None]:
        """
        Get account

        Args:
            accountId: account id

        Returns:
            (organization_name, email, active) or None (if account not found)
        """
        with engine.begin() as connection:
            query = Query([models.Account.organization_name, models.Account.email,
                           models.Account.active])
            query = query.filter(models.Account.account_id == accountId)

            account = connection.execute(query.statement).fetchone()
            return account

    @exceptionWrap
    def getAccountIdByEmail(self, email: str) -> Union[None, str]:
        """
        Get account id by email.
        Args:
            email: email of account

        Returns:

            None or account id
        """
        with engine.begin() as connection:
            query = Query([models.Account.account_id])
            query = query.filter(models.Account.email == email)
            account = connection.execute(query.statement).fetchone()
            return None if account is None else account[0]

    @exceptionWrap
    def getCountObjectWithFilters(self, row: Column, filters: BinaryExpression = None) -> int:
        """
        Get object count satisfy filters.
        Args:
            row: column
            filters: filters

        Returns:
            count
        """
        with engine.begin() as connection:
            query = Query([func.count(row).label('count')])
            if filters is not None:
                query = query.filter(filters)
            res = connection.execute(query.statement).fetchone()
            return res[0]

    @exceptionWrap
    def getCountAccounts(self) -> int:
        """
        Get count of accounts.

        Returns:
            count of account
        """
        return self.getCountObjectWithFilters(models.Account.account_id)

    @exceptionWrap
    def getCountTokens(self, accountId: Optional[str] = None) -> int:
        """
        Get token count of account or in system.
        Args:
            accountId: account id for filter

        Returns:
            token count
        """
        filters = and_(models.AccountToken.account_id == accountId)
        return self.getCountObjectWithFilters(models.AccountToken.token_id, filters)

    @exceptionWrap
    def getAccountTokens(self, accountId: str, page: int, pageSize: int) -> List[Tuple[str, str]]:
        """
        Get account tokens with pagination

        Args:
            accountId: account id
            page: page
            pageSize: page size

        Returns:
            list of tuples (token id, user data)
        """
        with engine.begin() as connection:
            query = Query([models.AccountToken.token_id, models.AccountToken.token_info])
            query = query.filter(models.AccountToken.account_id == accountId).offset((page - 1) * pageSize).limit(
                pageSize)

            tokensRes = connection.execute(query.statement).fetchall()
            return [(token[0], token[1]) for token in tokensRes]

    @exceptionWrap
    def getAccountIdByToken(self, tokenId: str) -> Union[None, str]:
        """
        Get account id by token.

        Args:
            tokenId: token id

        Returns:
            account id if it found otherwise None
        """
        with engine.begin() as connection:
            query = Query(models.AccountToken.account_id).filter(models.AccountToken.token_id == tokenId)
            accountId = connection.execute(query.statement).fetchone()
            if accountId is not None:
                return accountId[0]
            return None
