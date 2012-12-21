import os
import sys
import logging
import threading
from flask import Flask

ctx = threading.local()

def init_logging():
    logFormat = "%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s"
    logFormatter = logging.Formatter(fmt=logFormat)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(logFormatter)
    log = logging.getLogger(__name__)
    log.addHandler(logHandler)

init_logging()

app = Flask(__name__)

# This is required for sessions and message flashing
app.secret_key = os.urandom(24)

import pegasus.metrics.views

