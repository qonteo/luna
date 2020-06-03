from tornado import gen, ioloop
import tornado
import os
from tornado import locks
from tornado.options import OptionParser
import sys
from datetime import datetime
from lunavl import httpclient
import json


lock = locks.Lock()
cmdOptions = None


def getOptionsParser():
    op = OptionParser()
    op.define('src', help='source, folder with photos')
    op.define('luna_host', default="http://127.0.0.1", help='destination, ip address of luna python service')
    op.define('luna_port', default='5000', help='port of luna python service')
    op.define('luna_api', default=4, help='api version')
    op.define('lg', help='login to luna python server', type=str)
    op.define('psw', help='password to luna python server', type=str)
    op.define('list', help='list of account corresponding type, '
                             'if argument not set list, list will be created', type=str)
    op.define('c', help='level of concurrency', default=1, type=int)
    op.define('obj', help='type of object, person or descriptor', type=str)
    op.define('smf', help='skip images with several faces', default=False, type=bool)
    op.define('warped', help='is warped images', default=False, type=bool)
    op.define('sud', help='use file name as user_data. only when obj is person', default=False, type=bool)
    return op


def writeLog(msg, logFile, simpleMessage=False):
    with open(logFile, "a") as resFile:
        if simpleMessage is False:
            resFile.write(json.dumps(msg, sort_keys=True, indent=4))
            resFile.write(',\n')
        else:
            resFile.write(msg)
        resFile.close()


class Uploader:

    def __init__(self):
        requiredParameters = ["src", "lg", "psw", "obj"]

        for params in requiredParameters:
            if cmdOptions[params] is None:
                print("Requred parameter '{}' does not set".format(params))
                cmdOptions.print_help()
                exit(1)

        if cmdOptions["obj"] not in ("person", "descriptor"):
            print("wrong parameter 'obj', see correct arguments with argument '--help'")
            exit(1)
        if cmdOptions["obj"] == "person":
            self.personMode = True
        else:
            self.personMode = False

        self.waitPrepare = True

        self.files = []

        print("prepare a list of files for upload")
        for dirpath, dirnames, filenames in os.walk(cmdOptions["src"]):
            for filename in filenames:
                self.files.append(dirpath + "/" + filename)
        print("list of files is prepared, file count {}".format(len(self.files)))

        self.countProcessedFile = 0
        self.totalFiles = len(self.files)
        self.countSuccess = 0
        self.countFailed = 0
        self.countLinkedDescriptors = 0
        self.countFiledLinkedObjects = 0

        self.countWorkers = cmdOptions["c"]
        self.concurrency = cmdOptions["c"]

        self.skipMultiFace = cmdOptions["smf"]
        self.sendUserData = cmdOptions["sud"]
        self.warped = int(cmdOptions["warped"])

        self.errorLog = cmdOptions["lg"] + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_error.txt"
        self.successLog = cmdOptions["lg"] + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_success.txt"

        self.client = httpclient.LunaHttpClient(endPoint=cmdOptions["luna_host"],
                                                api=cmdOptions['luna_api'],
                                                port=cmdOptions['luna_port'],
                                                asyncRequest=True,
                                                login=cmdOptions["lg"], password=cmdOptions["psw"])


    @gen.coroutine
    def progress(self, isSuccess, bar_length = 20):
        with (yield lock.acquire()):
            self.countProcessedFile += 1
            count = self.countProcessedFile
        if isSuccess:
            self.countSuccess += 1
        else:
            self.countFailed += 1

        percent = float(count) / self.totalFiles
        hashes = '#' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))
        sys.stdout.write("\rProgress: [{0}] {1}%, upload {2} from {3}".format(hashes + spaces,
                                                                              int(round(percent * 100)),
                                                                              count, self.totalFiles))
        sys.stdout.flush()

    @gen.coroutine
    def errorLoadImage(self, msg):
        writeLog(msg, self.errorLog)
        yield self.progress(False)

    def initLog(self):
        for file in [self.errorLog, self.successLog]:
            writeLog('{\n', file, True)
            writeLog('\"Headers\":\n', file, True)
            writeLog({'login': cmdOptions["lg"], 'password': cmdOptions['psw'], 'list_id': self.listId}, file)
            if file is self.errorLog:
                writeLog('\"Error log\":\n', file, True)
            else:
                writeLog('\"Success log\":\n', file, True)
            writeLog('[\n', file, True)

    def closeLog(self):
        for file in [self.errorLog, self.successLog]:
            with open(file, 'rb+') as filehandle:
                buf = filehandle.readlines()[::-1][0]
                nonEmptyLog = ',' in str(buf)
                filehandle.seek(-2-(nonEmptyLog is True), os.SEEK_END)
                filehandle.truncate()
            writeLog(']}', file, True)

    @gen.coroutine
    def prepAndUpload(self):
        reply = yield self.client.getAccountData()
        if reply.statusCode > 300:
            print("failed check credentials")
            exit(3)

        listType = "persons" if self.personMode else "descriptors"
        if cmdOptions["list"] is None:
            listReply = yield self.client.createList(listType)
            if listReply.statusCode > 300:
                print("Failed create list, status code {}".format(listReply.statusCode))
                exit(2)
            self.listId = listReply.body["list_id"]
        else:
            self.listId = cmdOptions["list"]

        checkList = yield self.client.getList(self.listId)
        if checkList.statusCode > 300 or listType not in checkList.body:
            print("checking of list failed")
            exit(3)

        yield self.upload()

    @gen.coroutine
    def uploadPerson(self, descriptorId, filename):
        user_data = ""
        if self.sendUserData:
            user_data = ".".join(filename.split("/")[-1].split(".")[:-1])
        personIdReply = yield self.client.createPerson(user_data)
        if personIdReply.statusCode > 300:
            writeLog({'filename': filename, 'descriptorId': descriptorId, 'failed create person': personIdReply.body['detail']}, self.errorLog)
            self.countFiledLinkedObjects += 1
            return False

        personId = personIdReply.body["person_id"]

        linkPersonToPhotoReply = yield self.client.linkDescriptorToPerson(personId, descriptorId, 'attach')
        if linkPersonToPhotoReply.statusCode > 300:
            writeLog({'filename': filename, 'descriptorId': descriptorId, 'person': personId, 'failed link descriptor to person':
                        linkPersonToPhotoReply.body['detail']}, self.errorLog)
            self.countFiledLinkedObjects += 1
            return False

        linkPersonToListReply = yield self.client.linkListToPerson(personId, self.listId, 'attach')
        if linkPersonToListReply.statusCode > 300:

            writeLog({'filename': filename, 'person_id': personId,
                      "failed link person to list": linkPersonToListReply.body['detail']}, self.errorLog)
            self.countFiledLinkedObjects += 1
            return False
        self.countLinkedDescriptors += 1
        writeLog({'filename': filename, 'person_id': personId, 'descriptor_id': descriptorId}, self.successLog)
        return

    @gen.coroutine
    def uploadDescriptor(self, descriptorId, filename):
        linkDescriptorToListReply = yield self.client.linkListToDescriptor(descriptorId, self.listId, 'attach')
        if linkDescriptorToListReply.statusCode > 300:
            writeLog({'filename': filename, 'descriptor_id': descriptorId,
                      'failed link Descriptor To List': linkDescriptorToListReply.body['detail']},
                     self.errorLog)
            self.countFiledLinkedObjects += 1
        else:
            writeLog({'filename': filename, 'descriptor_id': descriptorId}, self.successLog)
            self.countLinkedDescriptors += 1

    @gen.coroutine
    def upload(self):
        self.initLog()

        it = iter(self.files)

        @gen.coroutine
        def worker():
            for img in it:
                yield self.uploadOneImg(img)
        yield [worker() for _ in range(self.concurrency)]

        self.closeLog()
        if self.personMode:
            print("\nEnd work, load {} person, failed to get descriptors from {} files, "
                  "failed create person from descriptor {}"
                  "".format(self.countLinkedDescriptors, self.countFailed,
                            self.countFiledLinkedObjects))
        else:
            print("\nEnd work, linked {} descriptors, failed to get descriptors from {} "
                  "files, failed link descriptors {}"
                  "".format(self.countLinkedDescriptors, self.countFailed,
                            self.countFiledLinkedObjects))

    @gen.coroutine
    def uploadOneImg(self, filename):
        try:
            uploadFileReply = yield self.client.extractDescriptors(filename=filename, warpedImage=self.warped)
            if uploadFileReply.statusCode > 300:
                yield self.errorLoadImage({'filename': filename,
                                           'error while loading image': uploadFileReply.body['detail']})
                return
            faces = uploadFileReply.body["faces"]
            if len(faces) == 0 or (len(faces) > 1 and self.skipMultiFace):
                yield self.errorLoadImage({'filename': filename, 'error face count': len(faces)})
                return
            for face in faces:
                if self.personMode:
                    yield self.uploadPerson(face["id"], filename)
                else:
                    yield self.uploadDescriptor(face["id"], filename)
            yield self.progress(True)
        except Exception as e:
            yield self.errorLoadImage({'filename': filename, "result": e})


if __name__ == '__main__':
    cmdOptions = getOptionsParser()
    cmdOptions.parse_command_line()
    uploader = Uploader()
    tornado.ioloop.IOLoop.current().run_sync(uploader.prepAndUpload)