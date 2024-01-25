import logging

from pegasus.metrics import db

log = logging.getLogger(__name__)

def migrate():
    cur = db.cursor()

    def drop_index(table, idx):
        cur.execute("SHOW INDEX FROM %s WHERE KEY_NAME='%s'" % (table, idx))
        if cur.fetchone():
            cur.execute("DROP INDEX %s ON %s" % (idx, table))

    drop_index("planner_metrics", "idx_planner_metrics_root_wf_uuid")
    cur.execute("create index idx_planner_metrics_root_wf_uuid on planner_metrics(root_wf_uuid)")

    drop_index("planner_metrics", "idx_planner_metrics_ts")
    cur.execute("create index idx_planner_metrics_ts on planner_metrics(ts)")

    db.commit()
    cur.close()
