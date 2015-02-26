/* We have to drop all tables before raw_data because all the tables
 * have a foreign key that links to raw_data
*/
drop table if exists invalid_data;
drop table if exists planner_metrics;
drop table if exists planner_errors;
drop table if exists downloads;
drop table if exists dagman_metrics;

drop table if exists raw_data;
create table raw_data (
    id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
    ts DOUBLE,
    remote_addr VARCHAR(15),
    data MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

create index idx_raw_data_ts on raw_data (ts);

create table invalid_data (
    id INTEGER UNSIGNED NOT NULL,
    error MEDIUMTEXT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

create table planner_metrics (
    id INTEGER UNSIGNED NOT NULL,
    ts DOUBLE,
    remote_addr VARCHAR(15),
    hostname VARCHAR(256),
    domain VARCHAR(256),
    version VARCHAR(10),
    wf_uuid VARCHAR(36),
    root_wf_uuid VARCHAR(36),
    start_time DOUBLE,
    end_time DOUBLE,
    duration FLOAT,
    exitcode SMALLINT,
    compute_tasks INTEGER UNSIGNED,
    dax_tasks INTEGER UNSIGNED,
    dag_tasks INTEGER UNSIGNED,
    total_tasks INTEGER UNSIGNED,
    chmod_jobs INTEGER UNSIGNED,
    inter_tx_jobs INTEGER UNSIGNED,
    compute_jobs INTEGER UNSIGNED,
    cleanup_jobs INTEGER UNSIGNED,
    dax_jobs INTEGER UNSIGNED,
    dag_jobs INTEGER UNSIGNED,
    so_tx_jobs INTEGER UNSIGNED,
    si_tx_jobs INTEGER UNSIGNED,
    create_dir_jobs INTEGER UNSIGNED,
    clustered_jobs INTEGER UNSIGNED,
    reg_jobs INTEGER UNSIGNED,
    total_jobs INTEGER UNSIGNED,
    data_config VARCHAR(15),
    application VARCHAR(256),
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

create index idx_planner_metrics_root_wf_uuid on planner_metrics(root_wf_uuid);

create table planner_errors (
    id INTEGER UNSIGNED NOT NULL,
    hash VARCHAR(32),
    error MEDIUMTEXT,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

create table downloads (
    id INTEGER UNSIGNED NOT NULL,
    ts DOUBLE,
    remote_addr VARCHAR(15),
    hostname VARCHAR(256),
    domain VARCHAR(256),
    version VARCHAR(10),
    filename VARCHAR(256),
    name VARCHAR(256),
    email VARCHAR(64),
    organization VARCHAR(256),
    app_domain VARCHAR(256),
    app_description VARCHAR(256),
    howheard MEDIUMTEXT,
    howhelp MEDIUMTEXT,
    oldfeatures MEDIUMTEXT,
    newfeatures MEDIUMTEXT,
    sub_users BOOLEAN,
    sub_announce BOOLEAN,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

create table dagman_metrics (
    id INTEGER UNSIGNED NOT NULL,
    ts DOUBLE,
    remote_addr VARCHAR(15),
    hostname VARCHAR(256),
    domain VARCHAR(256),
    version VARCHAR(10),
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
    planner_version VARCHAR(10),
    rescue_dag_number INTEGER,
    total_job_time DOUBLE,
    total_jobs INTEGER,
    total_jobs_run INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES raw_data(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

drop table if exists locations;
create table locations (
    ip VARCHAR(15) NOT NULL,
    country_code VARCHAR(256),
    country_name VARCHAR(256),
    region_code VARCHAR(256),
    region_name VARCHAR(256),
    city VARCHAR(256),
    zip_code VARCHAR(256),
    latitude DOUBLE,
    longitude DOUBLE,
    metro_code VARCHAR(256),
    PRIMARY KEY (ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;