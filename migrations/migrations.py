import sys
import optparse
import getpass
import MySQLdb as mysql
from MySQLdb.cursors import DictCursor

def connect():
    parser = optparse.OptionParser()
    parser.add_option("-H","--host",default="localhost",action="store",dest="host")
    parser.add_option("-P","--port",default=3307,action="store",dest="port",type="int")
    parser.add_option("-d","--db",default="pegasus_metrics",action="store",dest="db")
    parser.add_option("-u","--username",default="pegasus",action="store",dest="username")

    opts, args = parser.parse_args()

    if len(args) > 0:
        parser.error("Invalid argument")

    db = opts.db
    host = opts.host
    port = opts.port
    username = opts.username

    password = getpass.getpass("Database password for mysql://%s@%s:%s/%s: " % (username, host, port, db))

    if not password:
        sys.stderr.write("Specify password\n")
        exit(1)

    # Connect to the drupal database
    conn = mysql.connect(user=username,
                         passwd=password,
                         db=db,
                         host=host,
                         port=port,
                         cursorclass=DictCursor,
                         use_unicode=True)

    return conn

