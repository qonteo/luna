
import base64
import requests
import json

url_4buttons = "http://localhost:5002"


def createPayload(fileName):
    with open(fileName, "rb") as f:
        bytes = f.read()
        return bytes


def makePassportRequest(fileName):
    with open(fileName, "rb") as f:
        bytes = f.read()
        encoded = base64.b64encode(bytes)
    person = {'photo': encoded.decode('utf-8')}
    headers = {'Content-type': 'application/json'}
    str = '{"gender":"МУЖ.","number":"257730","authority":"ТП №2 В ГОР. МЫТИЩИ ОУФМС РОССИИ ПО МОСКОВСКОЙ ОБЛ. В МЫТИЩИНСКОМ Р-НЕ","patronymic":"ИГОРЕВИЧ","authority_code":"500-085","series":"4608","surname":"ДАНИЛОВ","birthdate":"31.05.1984","birthplace":"ГОР. ТАШКЕНТ РЕСП. УЗБЕКИСТАН","name":"ОЛЕГ"}'

    person['person'] = {"first_name": "TIM", "identification" :str}
    reply = requests.post(url = "{}/person?source=passport".format(url_4buttons), data = json.dumps(person, ensure_ascii = True), headers = headers)
    print(reply.status_code)
    print(reply.text)


def makeLunaRequest(fileName):
    headers = {"Content-Type": "image/jpeg"}
    url = url_4buttons + "/luna/storage/descriptors"
    binImage = createPayload(fileName)
    reply = requests.post(url, headers = headers,  data = binImage, params = {"warped_image": 0})
    print(reply.status_code, reply.text)
    return json.loads(reply.text)["faces"][0]["id"]


def createPerson():
    headers = {"Content-Type": "application/json"}
    payload = {"user_data": "login"}
    url = url_4buttons + "/luna/storage/persons"
    reply = requests.post(url, headers = headers, data = json.dumps(payload, ensure_ascii = True))
    while reply.status_code == 409:
        payload['user_data'] = payload['user_data'] + '1'
        reply = requests.post(url, headers = headers, data = json.dumps(payload, ensure_ascii = True))
    print(reply.status_code, reply.text)
    return json.loads(reply.text)["person_id"]


def attachDescriptorToPerson(descriptorId, personId):
    url = url_4buttons + "/luna/storage/persons/{}/linked_descriptors?do=attach&descriptor_id={}".format(personId,
                                                                                                      descriptorId)
    reply = requests.patch(url)
    print(reply.status_code, reply.text)


def uploadPerson(fileName):
    personId = createPerson()
    descriptorId = makeLunaRequest(fileName)
    attachDescriptorToPerson(descriptorId, personId)
    return personId


def search(fileName, personId):
    headers = {"Content-Type": "image/jpeg"}
    url = url_4buttons + "/matching/search?person_ids={}&source=stream".format(personId)
    binImage = createPayload(fileName)
    reply = requests.post(url, headers = headers, data = binImage)
    print(reply.status_code, reply.text)
    return json.loads(reply.text)["candidates"][0]["person_id"], json.loads(reply.text)["candidates"][0]["similarity"]


makePassportRequest("./test_2.jpg")

personId = uploadPerson("./test_2.jpg")
search("./test_1.jpg", personId)
