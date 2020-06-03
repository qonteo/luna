# -*- coding: utf-8 -*-
'''
Модуль инициализации.
'''
from flask import Flask
from flask_cors import CORS

from flask_socketio import SocketIO

async_mode = ""                         #: переменная, отвечающая за выбор режима асинхронной работы. В дебаге работаем с "threading", flask-трэдинг.\ eventlet использует  Monkey-path, доступно ещё "gevent" /сейчас не используется.

if __debug__:
    async_mode = "threading"
else:
    async_mode = 'eventlet'

if async_mode is None:
    try:
        import eventlet
        async_mode = 'eventlet'
    except ImportError:
        pass

    if async_mode is None:
        try:
            from gevent import monkey
            async_mode = 'gevent'
        except ImportError:
            pass

    if async_mode is None:
        async_mode = 'threading'

    print('async_mode is ' + async_mode)


if async_mode == 'eventlet':
    import eventlet
    eventlet.monkey_patch()
elif async_mode == 'gevent':
    from gevent import monkey
    monkey.patch_all()


app = Flask(__name__)
app.config.from_object('config')

CORS(app)


socketio = SocketIO(app, async_mode='eventlet')     #: http сервер для flask и web-сокетов.
from app import  view, receiver


def check_config():
    import config
    from requests import get
    headers = {"x-Auth-Token": config.LUNA2_TOKEN}

    reply = get('{}version'.format(config.LUNA2_URL))
    if reply.status_code != 200:
        raise RuntimeError('Wrong LUNA2_URL: "{}"'.format(config.LUNA2_URL))
    if reply.json()['Version']['luna_api']['api'] != config.LUNA2_API_VERSION:
        raise RuntimeError('Wrong LUNA2_API_VERSION: {}, right is: {}'.format(
            config.LUNA2_API_VERSION, reply.json()['Version']['luna_api']['api'])
        )

    for list_name in ('LIST_FOR_PASSPORTS', 'LIST_FOR_ID'):
        list_value = eval('config.' + list_name)
        reply = get('{}{}/storage/lists/{}'.format(config.LUNA2_URL, config.LUNA2_API_VERSION, list_value), headers=headers)
        if reply.status_code == 401:
            raise RuntimeError('Wrong LUNA2_TOKEN: "{}"'.format(config.LUNA2_TOKEN))
        elif reply.status_code == 404:
            raise RuntimeError('Wrong {}: "{}"'.format(list_name, list_value))
        if reply.status_code != 200:
            raise RuntimeError('Wrong reply status code on getting list {}: "{}"'.format(list_name, list_value))
        if "persons" not in reply.json():
            raise RuntimeError('Wrong list type {}: "{}", right is "persons"'.format(list_name, list_value))


check_config()
