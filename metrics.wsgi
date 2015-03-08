DBHOST = 'localhost'
DBPORT = 3306
DBUSER = 'pegasus'
DBPASS = 'pegasus'
DBNAME = 'pegasus_metrics'
DEBUG = False
VIRTUALENV = '/Users/juve/Workspace/pegasus-metrics/.pegasus-metrics'

execfile('%s/bin/activate_this.py' % VIRTUALENV, dict(__file__='%s/bin/activate_this.py' % VIRTUALENV))

from pegasus.metrics import app

app.config.from_object(__name__)

application = app

