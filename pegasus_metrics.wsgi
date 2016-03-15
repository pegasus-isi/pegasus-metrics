import sys
import os
import logging

# This activates the virtualenv for the wsgi process
#VIRTUALENV = '/Users/juve/Workspace/pegasus-metrics/.pegasus-metrics'
#execfile('%s/bin/activate_this.py' % VIRTUALENV, dict(__file__='%s/bin/activate_this.py' % VIRTUALENV))

# Alternatively, you can just add the package to the path
sys.path.insert(0, "/vagrant")

os.environ["PEGASUS_METRICS_CONFIG"] = "/vagrant/config.py"

from pegasus.metrics import app

logging.basicConfig(format=app.config["LOGFORMAT"], level=app.config["LOGLEVEL"])

application = app

