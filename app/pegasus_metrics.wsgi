import sys
import os
import logging

# Alternatively, you can just add the package to the path
sys.path.insert(0, "/srv/app")

os.environ["PEGASUS_METRICS_CONFIG"] = "/srv/app/config.py"

from pegasus.metrics import app

logging.basicConfig(format=app.config["LOGFORMAT"], level=app.config["LOGLEVEL"])

application = app

