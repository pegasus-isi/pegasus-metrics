try:
    import json
except ImportError:
    import simplejson as json
import requests

import migrations


conn = migrations.connect()

cur = conn.cursor()

cur.execute("""
create table locations (
    ip VARCHAR(15) NOT NULL,
    country_code VARCHAR(256),
    country_name VARCHAR(256),
    region_code VARCHAR(256),
    region_name VARCHAR(256),
    city VARCHAR(256),
    zip_code INTEGER UNSIGNED,
    latitude DOUBLE,
    longitude DOUBLE,
    metro_code INTEGER UNSIGNED,
    area_code INTEGER UNSIGNED,
    PRIMARY KEY (ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
""")
conn.commit()


cur.close()