# -*- coding: utf-8 -*-
'''
Модуль  приёма событий и раздачи уведомлений о них по iosocket
'''
from sqlalchemy.orm.exc import NoResultFound

from app import app

from flask_socketio import join_room, leave_room, \
    close_room, disconnect
from flask import stream_with_context

from app.db_functions import count_persons, add_person, get_person

app.config['SECRET_KEY'] = 'secret!vczs2231221f2q'
from flask_socketio import emit
import ujson as json
import requests
from config import NAMESPACE  #: namespace в котором работает web socket
from config import LIST_FOR_PASSPORTS, LIST_FOR_ID, LUNA2_TOKEN, LUNA2_URL, LUNA2_API_VERSION, \
    VERIFY_SIMILARITY_THRESHOLD
import base64
from flask import Response, request, jsonify
from app import socketio
from flask import make_response


def createAuthHeader(token):
    return {'X-Auth-Token': token}


def makeResponseFromReply(reply):
    response = Response(reply.content, reply.status_code, dict(reply.headers))
    return response


@socketio.on('join', namespace = NAMESPACE)
def join(message):
    '''
    Присоединение к room, доступен по socketio, 'join'  namespace=NAMESPACE.

    :param message: json с указание комнаты (поле 'room')
    '''
    join_room(message['room'])


@socketio.on('leave', namespace = NAMESPACE)
def leave(message):
    '''
    Отсаединение от room, доступен по socketio, 'leave'  namespace=NAMESPACE.

    :param message: json с указание комнаты (поле 'room')
    '''
    leave_room(message['room'])


@socketio.on('close room', namespace = NAMESPACE)
def close(message):
    '''
    Закрытие комнаты,  доступен по socketio, 'close room'  namespace=NAMESPACE.

    :param message: json с указание комнаты (поле 'room')
    '''
    close_room(message['room'])


@socketio.on('disconnect request', namespace = NAMESPACE)
def disconnect_request():
    '''
    Отсоединение от web socket, доступен по socketio, 'disconnect request'  namespace=NAMESPACE.
    :return:
    '''
    disconnect()


def createPerson(payload):
    headers = createAuthHeader(LUNA2_TOKEN)
    headers["Content-Type"] = "application/json"
    url = LUNA2_URL + "{}/storage/persons".format(LUNA2_API_VERSION)
    reply = requests.post(url, data = payload, headers = headers)
    return reply


def createDescriptors(binImg):
    headers = createAuthHeader(LUNA2_TOKEN)
    headers["Content-Type"] = "image/jpeg"
    url = LUNA2_URL + "{}/storage/descriptors".format(LUNA2_API_VERSION)
    reply = requests.post(url, data = binImg, headers = headers, params = request.args)
    return reply


def attachDescriptorToPerson(descriptorId, personId):
    headers = createAuthHeader(LUNA2_TOKEN)
    headers["Content-Type"] = "application/json"
    url = LUNA2_URL + "{}/storage/persons/{}/linked_descriptors?do=attach&descriptor_id={}".format(LUNA2_API_VERSION,
                                                                                                   personId,
                                                                                                   descriptorId)
    reply = requests.patch(url, data = request.data, headers = headers, params = request.args)
    return reply


def attachPersonToList(personId, listId):
    headers = createAuthHeader(LUNA2_TOKEN)
    headers["Content-Type"] = "application/json"
    url = LUNA2_URL + "{}/storage/persons/{}/linked_lists?do=attach&list_id={}".format(LUNA2_API_VERSION,
                                                                                       personId, listId)
    reply = requests.patch(url, data = request.data, headers = headers, params = request.args)
    return reply


@app.route('/matching/search', methods = ["POST"])
def search():
    source = request.args.get('source', None)
    if source == "stream":
        room = "stream_room"
    else:
        room = "mobile_room"

    app.logger.info("Room : {}".format(room))

    emit('event', {'data': {'data': "wait"}}, namespace = NAMESPACE, room = room)

    headers = createAuthHeader(LUNA2_TOKEN)
    headers["Content-Type"] = "image/jpeg"
    url = "{}{}/matching/search".format(LUNA2_URL, LUNA2_API_VERSION)
    reply = requests.post(url, data = request.data, headers = headers,
                          params={"list_id": LIST_FOR_ID, **request.args, 'estimate_attributes': 1})

    app.logger.info("Status code:{}, text: {}".format(reply.status_code, reply.text))

    if reply.status_code == 201:
        emit('event', {'data': {"data": json.loads(reply.text)}}, namespace = NAMESPACE, room = room)
    else:
        emit('event', {'data': "bad photo"}, namespace = NAMESPACE, room = room)

    return makeResponseFromReply(reply)


def get_headers():
    new_request_headers = {
        **createAuthHeader(LUNA2_TOKEN),
        **{
            k: request.headers[k]
            for k in ("X-Auth-Token", "Content-Type", "Authorization")
            if k in request.headers
        }
    }
    return new_request_headers


def before_create_person():
    # check user existence
    name = request.json.get('user_data', None)
    if name is None or count_persons(name):
        payload = json.dumps({
            "error_code": 42,
            "detail": 'Person with user_data "{}" already exist'.format(name)
        })
        return Response(payload, 409, content_type='application/json')


def after_create_person(reply):
    # add user
    add_person(request.json.get('user_data', None), reply.json()['person_id'], request.json.get('password', None))

    link_url = '{}{}/storage/persons/{}/linked_lists'.format(LUNA2_URL, LUNA2_API_VERSION,
                                                             reply.json()['person_id'])
    link_reply = requests.patch(link_url, headers=get_headers(), params={"list_id": LIST_FOR_ID, "do": "attach"})
    if link_reply.status_code != 204:
        app.logger.error(
            'Cannot link person {} with list {}'
            .format(reply.json()['person_id'], LIST_FOR_ID)
            .center(100, '!')
        )


def after_mobile_recognition(reply):
    similarity = reply.json()['candidates'][0]['similarity']
    if similarity >= VERIFY_SIMILARITY_THRESHOLD:
        emit('event', {'data': {"data": json.loads(reply.text)}}, namespace=NAMESPACE, room='mobile_room')
    else:
        emit('event', {'data': "bad photo"}, namespace=NAMESPACE, room='mobile_room')


def spy_decorator(handler):
    def wrap(path):
        # pre Luna API request
        if path == 'storage/persons' and request.method == 'POST':
            pre_response = before_create_person()
            if pre_response is not None:
                return pre_response
        # Luna API request
        reply = handler(path)
        # after Luna API request
        if path == 'storage/persons' and request.method == 'POST' and reply.status_code == 201:
            after_create_person(reply)
        elif path == 'matching/verify' and request.method == 'POST' and reply.status_code == 201:
            after_mobile_recognition(reply)
        return makeResponseFromReply(reply)
    return wrap


@app.route('/luna/<path:path>', methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@spy_decorator
def proxy(path):
    # proxy
    url = "{}{}/{}".format(LUNA2_URL, LUNA2_API_VERSION, path)
    headers = {"X-Auth-Token": LUNA2_TOKEN, **get_headers()}
    params = dict(request.args.items())
    data = request.data
    method = request.method

    reply = requests.request(method, url, headers=headers, params=params, data=data)
    return reply


@app.route('/persons', methods=["GET"])
def person():
    name = request.args.get('name', type=str)
    try:
        person = get_person(name)
    except NoResultFound:
        return Response('Not found', 404)
    result = {"name": name, "person_id": person.uuid, "password": person.password,
              "user_data": "_@login@_:{}_@pin@_:{}".format(name, person.password)}
    return jsonify(result)


def passportToStr(passportJs):
    res = ""
    for key in passportJs:
        res += "{}: {}, ".format(key, passportJs[key])
    # todo fix 128-length of user_data in LUNA_API
    return res[:128]


def uploadPerson():
    body = request.json
    photoBase64 = body['photo']
    binImage = base64.b64decode(photoBase64)
    payload = {"user_data": passportToStr(json.loads(request.json["person"]["identification"]))}

    descriptorReply = createDescriptors(binImage)
    descriptorId = json.loads(descriptorReply.text)["faces"][0]["id"]

    personReply = createPerson(json.dumps(payload))
    personId = json.loads(personReply.text)["person_id"]

    attachToPersonReply = attachDescriptorToPerson(descriptorId, personId)
    if attachToPersonReply.status_code != 204:
        return False, makeResponseFromReply(attachToPersonReply)

    attachToListReply = attachPersonToList(personId, LIST_FOR_PASSPORTS)
    if attachToListReply.status_code != 204:
        return False, makeResponseFromReply(attachToListReply)
    return True, (descriptorId, personId)


@app.route('/person', methods = ["POST"])
def addPerson():
    source = request.args.get('source', None)
    app.logger.info(source)

    if source != "passport":
        return Response(response = "Bad source", status = 400)

    uploadPersonRes, data = uploadPerson()
    if uploadPersonRes is False:
        return data
    descriptorId = data[0]

    emit('event', {'data': {'data': "wait"}}, namespace = NAMESPACE, room = "passport_room")

    url = "{}{}/matching/identify?descriptor_id={}&list_id={}".format(LUNA2_URL, LUNA2_API_VERSION, descriptorId,
                                                                      LIST_FOR_ID)
    headers = createAuthHeader(LUNA2_TOKEN)
    reply = requests.post(url, data = request.data, headers = headers, params = request.args)
    app.logger.info("Status code:{}, text: {}".format(reply.status_code, reply.text))

    if reply.status_code == 201:
        eventJs = json.loads(reply.text)
        eventJs["passport_data"] = request.json["person"]
        eventJs["passport_photo"] = request.json['photo']
        emit('event', {'data': {"data": eventJs}}, namespace = NAMESPACE, room = "passport_room")
    else:
        emit('event', {'data': "bad photo"}, namespace = NAMESPACE, room = "passport_room")
    return makeResponseFromReply(reply)
