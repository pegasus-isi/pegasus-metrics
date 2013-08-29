import json
import migrations

conn = migrations.connect()

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

