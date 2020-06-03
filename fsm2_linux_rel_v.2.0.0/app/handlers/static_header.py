from tornado.web import StaticFileHandler
from tornado import web
import os


class EventImgStaticHandler(StaticFileHandler):
    """
    Event image static handler.
    """
    @classmethod
    def get_absolute_path(cls, root, path):
        """
        Absolute path getter for event images.

        :param root: event images storage root directory
        :param path: event id
        :return: image address
        """
        eventId = path.split(os.path.sep)[-1]
        abspath = os.path.abspath(os.path.join(root, path))
        res = abspath.split(os.path.sep)
        path_ = eventId[-3:] + os.path.sep + eventId + ".jpg"
        image_address = os.path.sep.join(res[:-1]) + os.path.sep + path_
        return image_address

    @web.asynchronous
    def options(self, *args, **kwargs):
        """
        Options request handler.

        :param args: request args
        :param kwargs: request kwargs
        :return: None
        """
        self.set_status(200)
        self.finish()

    def set_default_headers(self):
        """
        Set default headers.

        :return: None
        """
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Credentials", 'true')
        self.set_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Auth-Token")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, PUT, OPTIONS, PATCH, DELETE')
