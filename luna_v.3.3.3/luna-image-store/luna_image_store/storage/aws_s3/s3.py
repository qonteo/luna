"""
Module for generate headers for requests to S3. Before using module you must be call *initS3Module*.

.. code-block:: python

   s3.initS3Module('https://s3.eu-central-1.amazonaws.com', 'portraits', 'AKIAJRKGS25RREXAMPLE', 
                   'YsC9dDiyA3JE18ATR3wusi9y7RMRItpjQEXAMPLE', 'eu-central-1')
   
   s3RestData = s3.S3("PUT", "/image.jpg", body)
   reply = requests.request("PUT", s3RestData.getUrl(), headers = s3RestData.getHeaders(), data = body)
   
   s3RestData = s3.S3("GET", "/image.jpg")
   reply = requests.request("GET", s3RestData.getUrl(), headers = s3RestData.getHeaders())
   
   s3RestData = s3.S3("POST", "/", body, "delete")
   reply = requests.request("POST", s3RestData.getUrl(), headers = s3RestData.getHeaders(), data = body)
   
This module was tested on three types of request - put object, get object, delete several object.

We don't support custom realization of s3. In this module  realize  both signature of authorization, default 's3v4', \
because  it is supported all servers of amazon. We suppose that user chose signature version2  of authorization \
if in initialization was setted signature which different of 's3v4'.
"""
import base64
import datetime
import hashlib
import hmac
from urllib.parse import urlsplit

from tornado import  gen
from tornado import httpclient
from tornado.httpclient import HTTPRequest
from configs.config import CONNECT_TIMEOUT, REQUEST_TIMEOUT

from hashlib import sha1
from email.utils import formatdate
from base64 import encodebytes

import boto3
from boto3.resources.base import ServiceResource

def _calculate_md5_from_file(inputBytes):
    """
    Function that realizes md5 calculation by byte image
    
    :param inputBytes: portrait in bytes.
    :return: md5
    """
    md5 = hashlib.md5()
    chunkSize = 1024 * 1024
    for i in range(int((len(inputBytes) + chunkSize - 1) / chunkSize)):
        chunk = inputBytes[i * chunkSize: min(len(inputBytes), (i + 1) * chunkSize)]

        md5.update(chunk)
    return md5.digest()


def getMD5(data):
    """
    Receive md5 in base64
    
    :param data: bytes
    :return: md5 in base64
    """
    binary_md5 = _calculate_md5_from_file(data)
    base64_md5 = base64.b64encode(binary_md5).decode('ascii')
    return base64_md5


# Key derivation functions. See:
# http://docs.aws.amazon.com/general/latest/gr/signature-v4-examples.html#signature-v4-examples-python
def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'aws4_request')
    return kSigning


def generateBodyForDeleteFromS3(fileList):
    res = '<?xml version="1.0" encoding="UTF-8"?><Delete>'
    for file in fileList:
        res += "<Object><Key>{}</Key></Object>".format(file)
    res += '</Delete>'
    return res


class S3:
    """
    Class for getting and storig headers and url for request to S3. 
    """

    S3_AWS_SECRET_ACCESS_KEY = ""
    S3_AWS_PUBLIC_ACCESS_KEY = ""
    S3_SIGNATURE_TYPE = ""
    S3_ENDPOINT = ""
    S3_HOST = ""
    S3_REGION = ""

    def __init__(self, method, url_path, bucketName, body = None, query_args = ""):
        """
        Init class and calculate headers for request.
        
        :param method: method of request (support "POST, GET, PUT, DELETE, PATCH, OPTION")
        :param url_path: path to resource, not including bucket
        :param body: body of request    
        :param query_args: string with qiery params  for request
        """

        t = datetime.datetime.utcnow()
        self.amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        self.date_stamp = t.strftime('%Y%m%d')  # Date w/o time, used in credential scope

        self.method = method

        self.body = body

        self.bucket = bucketName

        if body is not None:
            if type(body) is str:
                bytesBody = str.encode(body)
                self.md5Body = getMD5(bytesBody)
            else:
                self.md5Body = getMD5(body)
        else:
            self.md5Body = None

        # Step 2: Create canonical URI--the part of the URI from domain to query
        # string (use '/' if no path)
        self.canonical_uri = "/" + self.bucket + url_path
        self.url = S3.S3_ENDPOINT + self.canonical_uri

        # Step 3: Create the canonical query string. In this example, request
        # parameters are passed in the body of the request and the query string
        # is blank.
        self.canonical_querystring = query_args

        if S3.S3_SIGNATURE_TYPE != "s3v4":
            uri = self.canonical_uri
            if query_args != "":
                uri += "?" + query_args
            self.headers = S3.generateAWSAuthHeaderV2(method, uri, self.body)
            return

        # Step 4: Create the canonical headers. Header names must be trimmed
        # and lowercase, and sorted in code point order from low to high.
        # Note that there is a trailing \n.
        if body is None:
            self.canonical_headers = 'host:{}\nx-amz-content-sha256:UNSIGNED-PAYLOAD' \
                                     '\nx-amz-date:{}\n'.format(S3.S3_HOST, self.amz_date)
        else:
            self.canonical_headers = 'content-md5:{}\nhost:{}\nx-amz-content-sha256:UNSIGNED-PAYLOAD' \
                                     '\nx-amz-date:{}\n'.format(self.md5Body, S3.S3_HOST, self.amz_date)

        # Step 5: Create the list of signed headers. This lists the headers
        # in the canonical_headers list, delimited with ";" and in alpha order.
        # Note: The request can include any headers; canonical_headers and
        # signed_headers include those that you want to be included in the
        # hash of the request. "Host" and "x-amz-date" are always required.
        if body is None:
            self.signed_headers = 'host;x-amz-content-sha256;x-amz-date'
        else:
            self.signed_headers = 'content-md5;host;x-amz-content-sha256;x-amz-date'

        # Step 7: Combine elements to create create canonical request
        self.canonical_request = method + '\n' + self.canonical_uri + '\n' + self.canonical_querystring + '\n' \
                                        + self.canonical_headers + '\n' + self.signed_headers + '\n' \
                                        + 'UNSIGNED-PAYLOAD'

        self.algorithm = 'AWS4-HMAC-SHA256'
        self.credential_scope = self.date_stamp + '/' + S3.S3_REGION + '/' + 's3' + '/' + 'aws4_request'
        self.string_to_sign = self.algorithm + '\n' + self.amz_date + '\n' + self.credential_scope + '\n' \
                                             + hashlib.sha256(self.canonical_request.encode('utf-8')).hexdigest()

        # ************* TASK 3: CALCULATE THE SIGNATURE *************
        # Create the signing key using the function defined above.
        self.signing_key = getSignatureKey(S3.S3_AWS_SECRET_ACCESS_KEY, self.date_stamp, S3.S3_REGION, 's3')

        # Sign the string_to_sign using the signing_key
        self.signature = hmac.new(self.signing_key, self.string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        # ************* TASK 4: ADD SIGNING INFORMATION TO THE REQUEST *************
        # Put the signature information in a header named Authorization.
        self.authorization_header = self.algorithm + ' ' + 'Credential=' + S3.S3_AWS_PUBLIC_ACCESS_KEY + '/' \
                                                   + self.credential_scope + ', ' + 'SignedHeaders=' \
                                                   + self.signed_headers + ', ' + 'Signature=' + self.signature

        self.headers = {
            'X-Amz-Date': self.amz_date,
            'x-amz-content-sha256': 'UNSIGNED-PAYLOAD',
            'Authorization': self.authorization_header}
        if body is not None:
            self.headers['Content-MD5'] = self.md5Body

    @classmethod
    def initS3Module(cls, endpoint, access_key, secret_key, region = "", signature_type = 's3v4'):

        cls.S3_AWS_SECRET_ACCESS_KEY = secret_key
        cls.S3_AWS_PUBLIC_ACCESS_KEY = access_key
        cls.S3_SIGNATURE_TYPE = signature_type
        cls.S3_ENDPOINT = endpoint
        cls.S3_REGION = region
        cls.S3_HOST = urlsplit(cls.S3_ENDPOINT).hostname

    @staticmethod
    def generateAWSAuthHeaderV2(method, path, body = None):
        """
        Функция генерирующая  заголовок для авторизации в s3

        :param method: метод запроса в s3 (GET  или  PUT)
        :param path: id  дескриптора (имя файла, куда будет записана картинка).
        :param body: для того, чтобы положить картинку нужен md5 от неё
        :return: строчка с хедором
        """

        if body is not None:
            if type(body) is str:
                bytesBody = str.encode(body)
                md5Body = getMD5(bytesBody)
            else:
                md5Body = getMD5(body)
        else:
            md5Body = ""

        new_hmac = hmac.new(S3.S3_AWS_SECRET_ACCESS_KEY.encode('utf-8'),
                            digestmod = sha1)
        date = formatdate(usegmt = True)
        new_hmac.update((method + "\n" + md5Body + "\n\n" + str(date) + "\n" + path).encode('utf-8'))

        headers = {"Authorization": "AWS " + S3.S3_AWS_PUBLIC_ACCESS_KEY + ":" +
                                    encodebytes(new_hmac.digest()).strip().decode('utf-8'),
                   "Date": date}
        if md5Body != "":
            headers["Content-MD5"] = md5Body
        return headers

    def getHeaders(self):
        """
        Get headers for request to s3.
        
        Returns:
             dict with headers.
        """
        return self.headers

    def getUrl(self) -> str:
        """
        Get url for request to s3.
        
        Returns:
             url-string
        """
        return self.url + "?" + self.canonical_querystring

    @gen.coroutine
    def makeRequest(self):
        http_client = httpclient.AsyncHTTPClient()
        headers = self.getHeaders()
        url = self.getUrl()
        if self.canonical_querystring.find('delete') >= 0:
            headers['Content-Type'] = ''

        request = HTTPRequest(url = url,
                              method = self.method,
                              headers = headers,
                              request_timeout = REQUEST_TIMEOUT,
                              connect_timeout = CONNECT_TIMEOUT,
                              body = self.body)
        reply = yield http_client.fetch(request, raise_error = False)
        return reply

    @staticmethod
    def initClient() -> ServiceResource:
        """
        Create a resource service client.

        Returns:
            resource service client
        """
        session = boto3.session.Session()
        config = boto3.session.Config(signature_version='s3v4' if S3.S3_SIGNATURE_TYPE == 's3v4' else 's3')

        credentials = {
            'service_name': 's3',
            'aws_access_key_id': S3.S3_AWS_PUBLIC_ACCESS_KEY,
            'aws_secret_access_key': S3.S3_AWS_SECRET_ACCESS_KEY,
            'config': config
        }
        if S3.S3_REGION == "":
            credentials['endpoint_url'] = S3.S3_ENDPOINT
        else:
            credentials['region_name'] = S3.S3_REGION

        return session.resource(**credentials)

    @staticmethod
    def createBucket(bucketName, logger):
        s3Client = S3.initClient()
        location = {'CreateBucketConfiguration': {'LocationConstraint': S3.S3_REGION}} if S3.S3_REGION else {}
        try:
            s3Client.create_bucket(Bucket=bucketName, **location)
        except Exception as e:
            logger.exception()
            if hasattr(e, "response"):
                if 'Error' in e.response:
                    if 'Message' in e.response["Error"]:
                        return e.response["Error"]["Code"], e.response["Error"]["Message"]
            return "Unknown s3 code", "Unknown s3 error"
        return None, None

    @staticmethod
    def getBuckets(logger):
        s3Client = S3.initClient()
        try:
            return [i.name for i in s3Client.buckets.all()], None, None
        except Exception as e:
            logger.exception()
            if hasattr(e, "response"):
                if 'Error' in e.response:
                    if 'Message' in e.response["Error"]:
                        return [], e.response["Error"]["Code"], e.response["Error"]["Message"]
            return [], "Unknown s3 code", "Unknown s3 error"

    @staticmethod
    def deleteBucket(bucketName, logger):
        s3Client = S3.initClient()
        try:
            bucket = s3Client.Bucket(bucketName)
            bucket.objects.all().delete()
            bucket.delete()
        except Exception as e:
            logger.exception()
            if hasattr(e, "response"):
                if 'Error' in e.response:
                    if 'Message' in e.response["Error"]:
                        return e.response["Error"]["Code"], e.response["Error"]["Message"]
            return "Unknown s3 code", "Unknown s3 error"
        return None, None
