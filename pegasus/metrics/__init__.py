import sys
import logging
import threading

ctx = threading.local()

def init_logging():
    logFormat = "%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s"
    logFormatter = logging.Formatter(fmt=logFormat)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(logFormatter)
    log = logging.getLogger(__name__)
    log.addHandler(logHandler)

init_logging()

from flask import Flask

app = Flask(__name__)

import pegasus.metrics.views

