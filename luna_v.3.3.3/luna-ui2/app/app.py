import base64
from configparser import ConfigParser

from aiohttp import web

import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from aiohttp_graphql import GraphQLView
from graphql.execution.executors.asyncio import AsyncioExecutor
from schema import Schema

import settings
from views import extract_descriptor, proxy_portrait_image, bulk_extract, \
    handle_404, show_index, serve_static
from middlewares import error_pages
from error_formatter import format_luna_graphql_error


def setup_routes(app):
    static_regexp = '|.*\.'.join(['static', *settings.STATIC_FILES_EXTENSIONS])

    GraphQLView.attach(
        app, schema=Schema, graphiql=True,
        batch=True, executor=AsyncioExecutor(),
        error_formatter=format_luna_graphql_error
    )
    app.router.add_post('/extract/batch', bulk_extract)
    app.router.add_post('/extract', extract_descriptor)
    app.router.add_get('/portrait/{descriptor_id}', proxy_portrait_image)
    app.router.add_get('/{tail:(%s)}' % static_regexp, serve_static)
    app.router.add_get('/', show_index)


def read_config_file(config_section='DEFAULT'):
    config = ConfigParser()
    config.read(settings.CONFIG_FILE)
    return config[config_section]


def create_app():
    app = web.Application()
    configs = read_config_file()
    app.update(name='luna-graphql', **configs)
    secret_key = base64.urlsafe_b64decode(configs['cookie_secret'])
    aiohttp_session.setup(app, EncryptedCookieStorage(secret_key, cookie_name='_lecs'))
    error_middleware = error_pages({404: handle_404})
    app.middlewares.append(error_middleware)

    setup_routes(app)
    return app


if __name__ == '__main__':
    app = create_app()
    web.run_app(app, port=app['app_port'])
