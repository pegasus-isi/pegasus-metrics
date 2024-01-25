import json
import requests

from pegasus.metrics import db

url = 'http://metrics.pegasus.isi.edu/metrics'

def migrate():
    # Fetch all the download data
    cur = db.cursor()
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

        print(r["did"],r["filename"])

        # Post it to the metrics server
        resp = requests.post(url, data=json.dumps(d), headers={'content-type': 'application/json'})
        if resp.status_code != 202:
            print("ERROR:", resp.text)
            break

    cur.close()

