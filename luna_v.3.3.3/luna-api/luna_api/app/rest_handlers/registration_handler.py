import re
import ujson as json
from email.utils import parseaddr
from typing import Union

import tornado
from tornado import web

from crutches_on_wheels.errors.errors import Error
from crutches_on_wheels.errors.exception import VLException
from app.rest_handlers.base_handler_class import BaseRequestHandler


def parseJsonArg(inputJson: dict, field: str) -> Union[str, dict, list, int, float]:
    """
    Function to get arguments from JSON.

    Args:
        inputJson: input json(dict)
        field: required field.
    Returns:
        getting value
    """
    if not (field in inputJson):
        error = Error.formatError(Error.FieldNotInJSON, field)
        raise VLException(error, 400, False)
    arg = inputJson[field]
    if len(arg) == 0:
        error = Error.formatError(Error.EmptyField, field)
        raise VLException(error, 400, False)
    return arg


def validateEmail(email):
    """
    E-mail validation function
    
    :param email: str with email
    :return: True, if validation is successful, else False.
    """
    match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email)
    return False if match is None else True


def validatePassword(password: str) -> bool:
    """
    Validate length of password.

    Args:
        password: password

    Returns:
        True if length of password  is correct otherwise False
    """
    if not (8 <= len(password) <= 32):
        return True
    return False


class RegistrationHandler(BaseRequestHandler):
    """
    Handler to register accounts
    """

    @tornado.web.asynchronous
    @BaseRequestHandler.requestExceptionWrap
    def post(self):
        """
        Resource is available at '/accounts'

        .. http:post:: /accounts

            Request for registration.

            **Example request**:

            :reqheader LUNA-Request-Id: request id

            .. sourcecode:: http

                POST /accounts HTTP/1.1
                Accept: application/json

            .. json:object:: json for registration
                :showexample:

                :property organization_name: name of registration organization
                :proptype organization_name: user_name
                :property email: email of registration organization
                :proptype email: email
                :property password: password for access to account
                :proptype password: string
                :options  password: minlength=8,maxlength=32

            **Example response**:

            .. sourcecode:: http

                HTTP/1.1 201 Created
                Vary: Accept
                Content-Type: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            .. json:object:: response
                :showexample:

                :property token: token for access
                :proptype token: uuid4

            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 201: registration is successful
            :statuscode 409: e-mail is already taken
            :statuscode 400: request does not contain json
            :statuscode 400: password is too short or too long
            :statuscode 400: password field was not found in json
            :statuscode 400: password is empty
            :statuscode 400: email could not be parsed
            :statuscode 400: email was not found in json
            :statuscode 400: email is empty
            :statuscode 400: organization_name could not be parsed
            :statuscode 400: organization name is empty
            :statuscode 500: internal server error
        """
        reqJson = self.getInputJson()
        try:

            if reqJson is None:
                return self.error(400, Error.EmptyJson)
            name = parseJsonArg(reqJson, 'organization_name')

            password = parseJsonArg(reqJson, 'password')
            if validatePassword(password):
                return self.error(status_code=400, error=Error.PasswordBadLength)

            email = parseJsonArg(reqJson, 'email').lower()
            if not (validateEmail(parseaddr(email)[1])):
                return self.error(400, Error.IncorrectEmail)

        except ValueError:
            return self.error(400, Error.RequestNotContainsJson)

        accId, token = self.dbContext.registerAccount(name, email, password)
        payload = {"token": str(token)}
        self.write(json.dumps(payload, ensure_ascii=False))
        self.set_header('Content-Type', 'application/json')
        self.set_status(201)
        self.finish()
