# -*- coding: utf-8 -*-
CSRF_ENABLED = True
SECRET_KEY = 'k2Zz7d046fj5is92yDF'

LUNA2_URL = "http://127.0.0.1:5000/"                         #: url, по которому слушает Luna2 API
LUNA2_TOKEN = "71f9b3e0-51b1-480f-93b9-0e76e260bcbc"         #: token аккаунта Luna2 API
LUNA2_API_VERSION = 4

LIST_FOR_PASSPORTS = "9c51fac1-07db-4155-a2b0-d07c4f8c0e1e"  #: соответствующие списки Luna2 API
LIST_FOR_ID = "238bed9e-f2c2-4dc6-998b-6d08cec07ec2"

NAMESPACE = '/web_recognizer'                                #: namespace для socket io

VERIFY_SIMILARITY_THRESHOLD = 0.65
