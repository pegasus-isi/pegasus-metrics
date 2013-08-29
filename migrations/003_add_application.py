import MySQLdb as mysql
from MySQLdb.cursors import DictCursor
import json
import getpass

# stewie.isi.edu
#db = "pegasus_metrics"
#host = "localhost"
#username = "pegasus_metrics"

db = "pegasus_metrics"
host = "localhost"
username = "pegasus"

password = getpass.getpass("Database password for mysql://%s@%s/%s: " % (username, host, db))


# Connect to the drupal database
conn = mysql.connect(user=username,
                     passwd=password,
                     db=db,
                     host=host,
                     cursorclass=DictCursor,
                     use_unicode=True)


cur = conn.cursor()

cur.execute("ALTER TABLE planner_metrics ADD (application VARCHAR(256))")

conn.commit()

cur.close()

