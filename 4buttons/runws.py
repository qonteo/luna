# -*- coding: utf-8 -*-
__author__ = 'VisionLabs'
# !/bin/python3

from app import app

import sys

from app import socketio

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5002, debug=True, log_output=True)
