from version import VERSION

from .ss_handler import StatHandler
from .subscribe_handler import SubscribeHandler
from .login_handler import LoginHandler


def version_handler(request):
    """
    Handler for /version url
    :param request:
    :return:
    """
    return request.Response(code=200, json=VERSION)


HANDLERS = {
    '/api/events': StatHandler,
    '/api/subscribe': SubscribeHandler,
    '/version': version_handler,
    '/api/version': version_handler,
    '/login': LoginHandler,
}
