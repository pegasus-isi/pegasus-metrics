DBHOST = 'localhost'
DBUSER = 'pegasus'
DBPASS = 'pegasus'
DBNAME = 'pegasus_metrics'
DEBUG = False

from pegasus.metrics import app

app.config.from_object(__name__)

application = app

