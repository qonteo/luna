import re



def checkUUID4(uuidStr):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuidStr)
    if bool(match):
        return True
    else:
        return False


def createPayloadImg(pathToPhoto):
    with open(pathToPhoto, "rb") as f:
        imgBytes = f.read()
    return imgBytes
