class Response:
    def __init__(self, status_code = 200, content = None, headers = None):
        self.status_code = status_code
        self.content = content
        self.headers = headers

    @classmethod
    def fromHttpResponse(cls, request_response):
        response = cls()
        response.status_code = request_response.status_code
        if "Content-Type" in request_response.headers and request_response.headers["Content-Type"] == "application/json":
            response.content = request_response.json()
        else:
            response.content = request_response.content
        response.headers = request_response.headers
        return response