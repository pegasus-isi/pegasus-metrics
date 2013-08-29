import MySQLdb as mysql
from MySQLdb.cursors import DictCursor
import json
import requests
import getpass

url = 'http://metrics.pegasus.isi.edu/metrics'

db = "pegasus"
host = "stewie.isi.edu"
username = "pegasus"
password = getpass.getpass("Database password for mysql://%s@%s/%s:" % (username, host, db))

# Connect to the drupal database
conn = mysql.connect(user=username,
                     passwd=password,
                     db=db,
                     host=host,
                     cursorclass=DictCursor,
                     use_unicode=True)

# Fetch all the download data
cur = conn.cursor()
cur.execute("SELECT * FROM pegasus_download")
for r in cur.fetchall():
    # Convert it into a download metric
    d = {
       "type": "download",
       "client": "pegasus-download",
       "version": "0.1",
       "filename": r["filename"],
       "ts": r["timestamp"],
       "remote_addr": None,
       "name": r["name"],
       "email": r["email"],
       "organization": r["organization"],
       "sub_announce": bool(r["announce"]),
       "sub_users": bool(r["users"]),
       "app_domain": r["domain"],
       "app_description": r["application"],
       "oldfeatures": r["oldfeatures"],
       "newfeatures": r["newfeatures"],
       "howheard": r["howheard"],
       "howhelp": r["howhelp"]
    }
    
    print r["did"],r["filename"]
    
    # Post it to the metrics server
    resp = requests.post(url, data=json.dumps(d), headers={'content-type': 'application/json'})
    if resp.status_code != 202:
        print "ERROR:", resp.text
        break

cur.close()

