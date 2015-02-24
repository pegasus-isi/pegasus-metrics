try:
    import json
except ImportError:
    import simplejson as json
import requests
import logging
import migrations


log = logging.getLogger("pegasus.metrics.loader")
conn = migrations.connect()

cur = conn.cursor()
cur.execute("drop table if exists locations")
cur.execute("""
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
""")
conn.commit()

cur.execute("SELECT distinct(remote_addr) FROM raw_data ORDER BY ts desc")

uniqueIPs = cur.fetchall()
for ip in uniqueIPs:
    cur.execute("SELECT * from locations WHERE ip = %s", [ip['remote_addr']])
    if cur.fetchone() is not None or ip['remote_addr'] is None:
        continue
    try:
        r = requests.get('http://freegeoip.net/json/%s' % ip['remote_addr'])
        if 200 <= r.status_code < 300:
            r.encoding = 'utf-8'
            location = json.loads(r.text)
    except Exception, e:
        log.exception(e)
        log.warn("Error getting location for %s" % ip['remote_addr'])

    for key in location:
        if type(location[key]) == unicode:
            location[key] = location[key].encode('utf-8')

    if 'latitude' not in location or \
                    'longitude' not in location or \
                    'country_code' not in location or \
                    'region_code' not in location or \
                    'region_name' not in location or \
                    'city' not in location:
        continue
    if 'zip_code' not in location:
        location['zip_code'] = None

    if 'metro_code' not in location:
        location['metro_code'] = None

    cur.execute(
            """INSERT INTO locations (
            ip,
            country_code,
            country_name,
            region_code,
            region_name,
            city,
            zip_code,
            latitude,
            longitude,
            metro_code
        ) VALUES (
            %(ip)s,
            %(country_code)s,
            %(country_name)s,
            %(region_code)s,
            %(region_name)s,
            %(city)s,
            %(zip_code)s,
            %(latitude)s,
            %(longitude)s,
            %(metro_code)s
        )""", location)
    conn.commit()

cur.close()