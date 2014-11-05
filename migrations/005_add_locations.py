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
    zipcode INTEGER UNSIGNED,
    latitude DOUBLE,
    longitude DOUBLE,
    metro_code INTEGER UNSIGNED,
    area_code INTEGER UNSIGNED,
    PRIMARY KEY (ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
""")
conn.commit()

cur.execute("SELECT distinct(remote_addr) FROM planner_metrics")

uniqueIPs = cur.fetchall()
for ip in uniqueIPs:
    try:
        print ip['remote_addr']
        r = requests.get('http://freegeoip.net/json/%s' % ip['remote_addr'])
        if 200 <= r.status_code < 300:
            r.encoding = 'utf-8'
            location = json.loads(r.text)
    except:
        pass
    cur.execute(
        """INSERT INTO locations (
            ip,
            country_code,
            country_name,
            region_code,
            region_name,
            city,
            zipcode,
            latitude,
            longitude,
            metro_code,
            area_code
        ) VALUES (
            %(ip)s,
            %(country_code)s,
            %(country_name)s,
            %(region_code)s,
            %(region_name)s,
            %(city)s,
            %(zipcode)s,
            %(latitude)s,
            %(longitude)s,
            %(metro_code)s,
            %(area_code)s
        )""", location)
    conn.commit()

cur.close()