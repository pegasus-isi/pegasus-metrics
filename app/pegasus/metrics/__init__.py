import os
import sys
import logging
import threading
from flask import Flask

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.config.from_envvar("PEGASUS_METRICS_CONFIG")

# This is required for sessions and message flashing
app.secret_key = os.urandom(24)

import pegasus.metrics.views
import pegasus.metrics.filters

