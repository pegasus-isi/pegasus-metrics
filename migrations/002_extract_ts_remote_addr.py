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

password = getpass.getpass("Database password for mysql://%s@%s/%s:" % (username, host, db))


# Connect to the drupal database
conn = mysql.connect(user=username,
                     passwd=password,
                     db=db,
                     host=host,
                     cursorclass=DictCursor,
                     use_unicode=True)


updates = []

cur = conn.cursor()

cur.execute("ALTER TABLE raw_data ADD (ts DOUBLE, remote_addr VARCHAR(15))")

cur.execute("SELECT id, ts, remote_addr, data FROM raw_data")
for r in cur.fetchall():
    jsontxt = r["data"]
    jsonobj = json.loads(jsontxt)
    objid = r["id"]
    ts = r["ts"]
    if ts is None:
        ts = jsonobj["ts"]
    remote_addr = r["remote_addr"]
    if remote_addr is None:
        remote_addr = jsonobj["remote_addr"]

    updates.append([ts, remote_addr, objid])

cur.executemany("UPDATE raw_data SET ts=%s, remote_addr=%s WHERE id=%s", updates)

conn.commit()

cur.close()

