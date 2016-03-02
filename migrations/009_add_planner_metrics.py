import migrations

conn = migrations.connect()

cur = conn.cursor()

cur.execute("alter table planner_metrics add uses_pmc BOOLEAN")
cur.execute("alter table planner_metrics add planner_args TEXT")
cur.execute("alter table planner_metrics add deleted_tasks INTEGER UNSIGNED")

conn.commit();

cur.close();
