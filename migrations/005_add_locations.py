try:
    import json
except ImportError:
    import simplejson as json
import requests
import logging
import migrations

logging.basicConfig()

log = logging.getLogger()
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

cur.execute("SELECT distinct(remote_addr) FROM raw_data WHERE remote_addr is not NULL ORDER BY ts desc")
locations = []
for ip in cur:
    addr = ip['remote_addr']
    location = None
    try:
        r = requests.get('http://gaul.isi.edu:8192/json/%s' % addr)
        if 200 <= r.status_code < 300:
            r.encoding = 'utf-8'
            location = json.loads(r.text)
        else:
            log.error("Error getting location for %s: Status %s" % (addr, r.status_code))
            exit(1)
    except Exception, e:
        log.error("Error getting location for %s" % addr)
        log.exception(e)
        exit(1)

    for key in location:
        if type(location[key]) == unicode:
            location[key] = location[key].encode('utf-8')

    if 'latitude' not in location or \
                    'longitude' not in location or \
                    'country_code' not in location or \
                    'region_code' not in location or \
                    'region_name' not in location or \
                    'city' not in location:
        log.error("Location for %s missing something: %s" % (addr, location))
        exit(1)

    if 'zip_code' not in location:
        location['zip_code'] = None

    if 'metro_code' not in location:
        location['metro_code'] = None

    locations.append(location)

# Insert all the locations at once
cur.executemany(
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
    )""", locations)

# One transaction
conn.commit()

cur.close()
