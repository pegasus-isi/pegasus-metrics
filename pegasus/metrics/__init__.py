import os
import sys
import logging
import threading
from flask import Flask
#try:
#    import json
#except ImportError:
#    import simplejson as json
#from decimal import Decimal

ctx = threading.local()

def init_logging():
    logFormat = "%(levelname)s %(filename)s:%(lineno)s %(message)s"
    logFormatter = logging.Formatter(fmt=logFormat)
    logHandler = logging.StreamHandler()
    logHandler.setFormatter(logFormatter)
    log = logging.getLogger(__name__)
    log.addHandler(logHandler)

init_logging()

#class PegasusJSONEncoder(json.JSONEncoder):
#    def default(self, obj):
#        if isinstance(obj, Decimal):
#            # Convert decimal instances to strings.
#            return str(obj)
#        return super(self, PegasusJSONEncoder).default(obj)

app = Flask(__name__)
#app.json_encoder = PegasusJSONEncoder

# This is required for sessions and message flashing
app.secret_key = os.urandom(24)

import pegasus.metrics.views
import pegasus.metrics.filters

