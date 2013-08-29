import migrations

conn = migrations.connect()

cur = conn.cursor()

cur.execute("ALTER TABLE planner_metrics ADD (application VARCHAR(256))")

conn.commit()

cur.close()

