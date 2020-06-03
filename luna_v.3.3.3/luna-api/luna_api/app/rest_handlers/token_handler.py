from tornado import web

from app.rest_handlers.storage_handlers import StorageHandler
from crutches_on_wheels.errors.errors import Error


class TokenHandler(StorageHandler):
    """
    Handler to work with the token.
    """

    @web.asynchronous
    @StorageHandler.requestExceptionWrap
    def get(self, token_id):
        """
        Resource to get token data
        
        .. http:get:: /account/tokens/{token_id}
        
            :param token_id: token id
            
            **Example request**:

            :reqheader Authorization: basic authorization

            **Example response**:
          
            :statuscode 200:  token data is received successfully
            
            .. sourcecode:: http
            
               HTTP/1.1 200 Ok
               Vary: Accept
               Content-Type: application/json

            Token data must be presented in format :json:object:`token_data`.

            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 404: token not found
            :statuscode 500: internal server error

        """
        tokenRes = self.dbContext.getTokenById(token_id, self.accountId)
        self.success(200, outputJson={"token_data": tokenRes})

    @web.asynchronous
    @StorageHandler.requestExceptionWrap
    def patch(self, token_id):
        """
        Resource to change token data
        
        .. http:patch:: /account/tokens/{token_id}
            
            :param token_id: token id
        
            **Example request**:

            :reqheader Authorization: basic authorization

            :reqheader LUNA-Request-Id: request id
  
            :statuscode 204: token is changed successfully
            
            .. sourcecode:: http

                POST /storage/tokens/{token_id} HTTP/1.1
                Accept: application/json
                LUNA-Request-Id: 1516179740,c06887a2

            Token data must be presented in format :json:object:`token_data`.

            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 400: field *token_data* is too large
            :statuscode 400: field *token_data* has wrong type, *string* type is required
            :statuscode 400: descriptor not found
            :statuscode 500: internal server error

        """
        existTokenRes = self.dbContext.checkTokenExist(token_id, self.accountId)

        if not existTokenRes:
            return self.error(404, Error.TokenNotFound)
        info = self.getInfoFromRequest("token_data", True)
        if type(info) != str:
            error = Error.formatError(Error.BadTypeOfFieldInJSON, 'token_data', 'string')
            return self.error(400, error)
        if len(info) > 128:
            return self.error(400, Error.BigUserData)

        self.dbContext.updateTokenInfo(token_id, self.accountId, info)

        self.success(204)

    @web.asynchronous
    @StorageHandler.requestExceptionWrap
    def delete(self, token_id):
        """
        Resource to delete token data
        
        .. http:delete:: /account/tokens/{token_id}

            :param token_id: token id

            **Example request**:

            :reqheader LUNA-Request-Id: request id

            :reqheader Authorization: basic authorization

            **Example response**:
          
            :statuscode 204: token was deleted successfully
            
            .. sourcecode:: http 
            
               HTTP/1.1 204 Ok
               Vary: Accept
               Content-Type: application/json
               
            Error message is returned in format :json:object:`server_error`.
            
            :statuscode 404: token not found
            :statuscode 500: internal server error

        """
        existTokenRes = self.dbContext.checkTokenExist(token_id, self.accountId)

        if not existTokenRes:
            return self.error(404, existTokenRes)

        self.dbContext.removeTokens([token_id], self.accountId)

        self.success(204)
