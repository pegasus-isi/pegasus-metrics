from pegasus.metrics import db

def migrate():
    cur = db.cursor()

    cur.execute("""
    create table dagman_metrics (
        id INTEGER UNSIGNED NOT NULL,
        ts DOUBLE,
        remote_addr VARCHAR(15),
        hostname VARCHAR(256),
        domain VARCHAR(256),
        version VARCHAR(32),
        wf_uuid VARCHAR(36),
        root_wf_uuid VARCHAR(36),
        start_time DOUBLE,
        end_time DOUBLE,
        duration FLOAT,
        exitcode SMALLINT,
        dagman_id VARCHAR(32),
        parent_dagman_id VARCHAR(32),
        jobs INTEGER,
        jobs_failed INTEGER,
        jobs_succeeded INTEGER,
        dag_jobs INTEGER,
        dag_jobs_failed INTEGER,
        dag_jobs_succeeded INTEGER,
        dag_status INTEGER,
        planner VARCHAR(1024),
        planner_version VARCHAR(32),
        rescue_dag_number INTEGER,
        total_job_time DOUBLE,
        total_jobs INTEGER,
        total_jobs_run INTEGER,
        PRIMARY KEY (id),
        FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
    """)

    db.commit()

    cur.close()

