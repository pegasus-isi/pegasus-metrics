import logging
import migrations

logging.basicConfig()

log = logging.getLogger()

conn = migrations.connect()

cur = conn.cursor()

def drop_index(table, idx):
    cur.execute("SHOW INDEX FROM %s WHERE KEY_NAME='%s'" % (table, idx))
    if cur.fetchone():
        cur.execute("DROP INDEX %s ON %s" % (idx, table))

drop_index("planner_metrics", "idx_planner_metrics_root_wf_uuid")
cur.execute("create index idx_planner_metrics_root_wf_uuid on planner_metrics(root_wf_uuid)")

drop_index("planner_metrics", "idx_planner_metrics_ts")
cur.execute("create index idx_planner_metrics_ts on planner_metrics(ts)")

conn.commit()
cur.close()
