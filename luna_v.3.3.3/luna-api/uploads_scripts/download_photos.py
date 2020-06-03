from tornado import gen, httpclient, ioloop
import tornado
import os, sys
from tornado.options import OptionParser
from lunavl import httpclient
from tornado import locks


lock = locks.Lock()
cmdOptions = None


def getOptionsParser():
    op = OptionParser()
    op.define('dst', help='source, folder with persons')
    op.define('luna_host', default="http://127.0.0.1", help='destination, ip address of luna python service')
    op.define('luna_port', default='5000', help='port of luna python service')
    op.define('luna_api', default=4, help='api version')
    op.define('lg', help='login to luna python server', type=str)
    op.define('psw', help='password to luna python server', type=str)
    op.define('c', help='level of concurrency', default=5, type=int)
    return op


class Downloader:
    def __init__(self):
        self.currentPosition = 0
        self.countFile = 0
        self.countSuccess = 0
        self.countFailed = 0
        self.totalFiles = None
        self.concurrency = cmdOptions["c"]
        self.folder = cmdOptions["dst"]
        self.client = httpclient.LunaHttpClient(endPoint=cmdOptions["luna_host"], api=cmdOptions['luna_api'],
                                                port=cmdOptions['luna_port'], asyncRequest=True, login=cmdOptions["lg"],
                                                password=cmdOptions["psw"])
        if not os.path.exists(self.folder):
            print('Folder', self.folder, 'does not exists')
            exit(1)

    @gen.coroutine
    def progress(self, isSuccess, bar_length=20):
        with (yield lock.acquire()):
            self.countFile += 1
            count = self.countFile
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
    def downloadOneFile(self, descriptorId):
        reply = yield self.client.getPortrait(descriptorId)
        if reply.statusCode == 200:
            with open(self.folder + "/" + descriptorId + ".jpg", 'wb') as f:
                f.write(reply.body)
                yield self.progress(True)
        else:
            yield self.progress(False)

    @gen.coroutine
    def downloadFiles(self):
        self.currentPosition += 1
        i = self.currentPosition
        reply = yield self.client.getDescriptors(page=i, pageSize=10)
        if self.totalFiles is None:
            self.totalFiles = reply.body['count']
        if reply.statusCode == 200:
            if 'descriptors' in reply.body and len(reply.body['descriptors']):
                for descriptor in reply.body["descriptors"]:
                    yield self.downloadOneFile(descriptor["id"])
                yield self.downloadFiles()
        else:
            yield self.downloadFiles()

    @gen.coroutine
    def download(self):
        yield [self.downloadFiles() for _ in range(self.concurrency)]
        print('\nCount of success downloads:', self.countSuccess)
        print('Failed to download:', self.countFailed)


if __name__ == '__main__':
    cmdOptions = getOptionsParser()
    cmdOptions.parse_command_line()
    downloader = Downloader()
    tornado.ioloop.IOLoop.current().run_sync(downloader.download)
