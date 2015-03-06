
import migrations

conn = migrations.connect()

cur = conn.cursor()

cur.execute("alter table planner_metrics modify version VARCHAR(32)")
cur.execute("alter table downloads modify version VARCHAR(32)")
cur.execute("alter table dagman_metrics modify version VARCHAR(32)")
cur.execute("alter table dagman_metrics modify planner_version VARCHAR(32)")

conn.commit();

cur.close();