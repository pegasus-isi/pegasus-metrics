# This activates the virtualenv for the wsgi process
VIRTUALENV = '/Users/juve/Workspace/pegasus-metrics/.pegasus-metrics'
execfile('%s/bin/activate_this.py' % VIRTUALENV, dict(__file__='%s/bin/activate_this.py' % VIRTUALENV))

from pegasus.metrics import app

application = app

