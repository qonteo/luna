from tornado import gen, ioloop
import tornado
import os
from tornado import locks
from tornado.options import OptionParser
import sys
from datetime import datetime
from time import time
from lunavl import httpclient
import json


cmdOptions = None

lock = locks.Lock()


def getOptionsParser():
    op = OptionParser()
    op.define('src', help='source, folder with persons')
    op.define('luna_host', default="http://127.0.0.1", help='destination, ip address of luna python service')
    op.define('luna_port', default='5000', help='port of luna python service')
    op.define('luna_api', default=4, help='api version')
    op.define('lg', help='login to luna python server', type=str)
    op.define('psw', help='password to luna python server', type=str)
    op.define('wList', help='does not attach persons to list, default False', default=False, type=bool)
    op.define('list', help='persons list of account, if  it does not set and wList does not set, '
                             'list will be created', type=str)
    op.define('mdp', default=-1, help='max descriptors on 1 person, -1 - all', type=int)
    op.define('c', help='level of concurrency', default=1, type=int)
    op.define('sud', help='use folder name as user_data.', default=False, type=bool)
    op.define('warped', help='is warped images', default=False, type=bool)
    return op


def writeLog(msg, logFile, simpleMessage=False):
    with open(logFile, "a") as resFile:
        if simpleMessage is False:
            resFile.write(json.dumps(msg, sort_keys=True, indent=4))
            resFile.write(',\n')
        else:
            resFile.write(msg)
        resFile.close()


def createLogMsg(success, failed, personId, folder):
    msg = {"person_path": folder, "personId": personId, "upload": str(len(success)),
           "linked images": [suc for suc in success], "failed_count": str(len(failed)),
           "failed": [fail for fail in failed]
           }
    return msg


class Uploader:
    def __init__(self):
        requiredParameters = ["src", "lg", "psw"]

        for params in requiredParameters:
            if cmdOptions[params] is None:
                print("Requred parameter '{}' does not set".format(params))
                cmdOptions.print_help()
                exit(1)

        self.countProcessedFolder = 0
        self.countSuccess = 0
        self.countLinkDescriptors = 0
        self.countPersonsWithDescriptors = 0
        self.countFailed = 0
        self.concurrency = cmdOptions["c"]
        self.countWorkers = cmdOptions["c"]
        self.folders = []
        self.filenames = []

        self.maxPhotos = cmdOptions["mdp"]

        self.waitPrepare = True

        self.sendUserData = cmdOptions["sud"]
        self.warped = int(cmdOptions["warped"])

        self.authHeader = {'login': cmdOptions["lg"], 'password': cmdOptions["psw"]}
        self.lunaUrl = cmdOptions["luna_host"]

        self.errorLog = cmdOptions["lg"] + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_error.txt"
        self.successLog = cmdOptions["lg"] + "_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_success.txt"

        self.withoutList = cmdOptions["wList"]

        self.client = httpclient.LunaHttpClient(endPoint=cmdOptions["luna_host"], asyncRequest=True,
                                                api=cmdOptions['luna_api'],
                                                port=cmdOptions['luna_port'],
                                                login=cmdOptions["lg"], password=cmdOptions["psw"])

        print("Start prepare data for upload")
        for dirpath, dirnames, filenames_in_dir in os.walk(cmdOptions["src"]):
            self.folders.extend([dirpath + '/' + dirname for dirname in dirnames])

        self.totalPersons = len(self.folders)

        self.countSuccessPhoto, self.successUploadImage, self.failedUploadImage = {}, {}, {}

        print("list of folders is prepared, folders count {}".format(self.totalPersons))

    def initLog(self):
        for file in [self.errorLog, self.successLog]:
            writeLog('{\n', file, True)
            writeLog('\"Headers\":\n', file, True)
            hdrs = {'login': cmdOptions["lg"], 'password': cmdOptions['psw']}
            if not cmdOptions["wList"]:
                hdrs["list_id"] = self.listId
            writeLog(hdrs, file)
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

        if not cmdOptions["wList"]:
            if cmdOptions["list"] is None:

                listReply = yield self.client.createList('persons')
                if listReply.statusCode > 300:
                    print("Failed create list, status code {}".format(listReply.statusCode))
                    exit(2)
                self.listId = listReply.body["list_id"]
            else:
                self.listId = cmdOptions["list"]

            if not self.client.getList('persons'):
                print("checking of list failed")
                exit(3)
        else:
            self.listId = None

        yield self.upload()


    @gen.coroutine
    def progress(self, isSuccess, bar_length = 20):
        with (yield lock.acquire()):
            self.countProcessedFolder += 1
            count = self.countProcessedFolder
        if isSuccess:
            self.countSuccess += 1
        else:
            self.countFailed += 1

        percent = float(count) / self.totalPersons
        hashes = '#' * int(round(percent * bar_length))
        spaces = ' ' * (bar_length - len(hashes))
        sys.stdout.write("\rProgress: [{0}] {1}%, upload {2} from {3}".format(hashes + spaces,
                                                                              int(round(percent * 100)),
                                                                              count, self.totalPersons))
        sys.stdout.flush()

    @gen.coroutine
    def upload(self):
        self.initLog()

        it = iter(self.folders)

        @gen.coroutine
        def worker():
            for folder in it:
                yield self.uploadPerson(folder)
        yield [worker() for _ in range(self.concurrency)]

        self.closeLog()
        print(
        "\nEnd work. {} persons was created from {} folders. {} descriptors was linked to persons. "
        "{} persons with descriptors".format(self.countSuccess, self.totalPersons,
                                             self.countLinkDescriptors,
                                             self.countPersonsWithDescriptors))

    @gen.coroutine
    def uploadPerson(self, folder):
        try:
            user_data = ""
            person = folder.split("/")[-1]
            if self.sendUserData:
                user_data = person

            reply = yield self.client.createPerson(user_data)

            if reply.statusCode > 300:
                yield self.progress(False)

            personId = reply.body["person_id"]

            if not self.withoutList:
                reply = yield self.client.linkListToPerson(personId, self.listId, 'attach')
                if reply.statusCode > 300:
                    writeLog({'person': person, 'error': 'failed link person to list'}, self.errorLog)
                    yield self.progress(False)
                    yield self.uploadPerson()
                    return

            self.countSuccessPhoto[person] = 0
            self.successUploadImage[person] = []
            self.failedUploadImage[person] = []

            files = [file for file in os.listdir(folder) if os.path.isfile(os.path.join(folder, file))]
            for file in files:
                yield self.uploadOneImgAndLinkToPerson(file, person, personId, folder)
            if self.countSuccessPhoto[person] > 0:
                self.countPersonsWithDescriptors += 1
            msg = createLogMsg(self.successUploadImage[person], self.failedUploadImage[person], personId, folder)
            writeLog(msg, self.successLog)
            yield self.progress(True)
        except Exception as e:
            writeLog({'error with person': person, 'error description:': str(e)}, self.errorLog)
            yield self.progress(False)

    @gen.coroutine
    def uploadOneImgAndLinkToPerson(self, filename, person, personId, path):
        reply = yield self.client.extractDescriptors(filename=os.path.join(path, filename), warpedImage=self.warped)
        if reply.statusCode > 300:
            error = {'filename': filename, 'person': personId, 'error while loading image': reply.body['detail']}
            writeLog(error, self.errorLog)
            self.failedUploadImage[person].append(error)
            return

        faces = reply.body["faces"]
        if len(faces) != 1:
            error = {'filename': filename, 'person': personId, 'error face count': str(len(faces))}
            writeLog(error, self.errorLog)
            self.failedUploadImage[person].append(error)
            return

        photoId = reply.body["faces"][0]["id"]

        reply = yield self.client.linkDescriptorToPerson(personId, photoId, 'attach')
        if reply.statusCode > 300:
            error = {filename: "failed link descriptor {} to person {}, {}"
                               "".format(personId, photoId, reply.body['detail'])}
            writeLog(error, self.errorLog)
            self.failedUploadImage[person].append(error)
            return
        self.successUploadImage[person].append(filename + ", descriptor_id: " + photoId)
        self.countSuccessPhoto[person] += 1
        self.countLinkDescriptors += 1


if __name__ == '__main__':
    cmdOptions = getOptionsParser()
    cmdOptions.parse_command_line()
    uploader = Uploader()
    start = time()
    tornado.ioloop.IOLoop.current().run_sync(uploader.prepAndUpload)
    print("\nupload time:", time() - start)
