import os
import unittest
import MySQLdb as mysql
import ast

from pegasus.metrics import app, ctx, db

__author__ = 'dcbriggs'

def relfile(filename):
    d = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(d, filename))

class MetricsTestCase(unittest.TestCase):

    def setUp(self):
        app.config["DBHOST"] = 'localhost'
        app.config["DBPORT"] = 3306
        app.config["DBUSER"] = 'pegasus'
        app.config["DBPASS"] = 'pegasus'
        app.config['DBNAME'] = 'test_metrics'

        app.config['TESTING'] = True
        self.app = app.test_client()

        db.connect(host=app.config["DBHOST"],
                        port=app.config["DBPORT"],
                        user=app.config["DBUSER"],
                        passwd=app.config["DBPASS"],
                        db="")
        with ctx.db.cursor() as cur:
            create_db = "create database if not exists %s " % (app.config["DBNAME"])
            cur.execute(create_db)
            select_db = "use %s " % (app.config['DBNAME'])
            cur.execute(select_db)

            with open(relfile('../schema.sql'), 'r') as schemaFile:
                schema = schemaFile.read().split(';')
                for command in schema:
                    if command:
                        cur.execute(command)


    def tearDown(self):
        db.connect(host=app.config["DBHOST"],
                   port=app.config["DBPORT"],
                   user=app.config["DBUSER"],
                   passwd=app.config["DBPASS"],
                   db="")
        with ctx.db.cursor() as cur:
            drop_db = "drop database if exists %s" % (app.config["DBNAME"])
            cur.execute(drop_db)

    def test_index_html(self):
        rv = self.app.get('/')

    def test_add_planner_metric(self):
        with open(relfile('metrics.json'), 'r') as rawMetric:
            data = rawMetric.read()
            rv = self.app.post('/metrics', data=data, headers={'Content-Type' : 'application/json'})
            assert rv.data == ''

            db.connect(host=app.config["DBHOST"],
                       port=app.config["DBPORT"],
                       user=app.config["DBUSER"],
                       passwd=app.config["DBPASS"],
                       db=app.config["DBNAME"])
            with ctx.db.cursor() as cur:
                # The test data should be added to only the raw_data, planner_metrics, and locations tables
                cur.execute('select count(*) from raw_data')
                rawDataCount = int(cur.fetchone()['count(*)'])
                assert rawDataCount == 1

                cur.execute('select * from planner_metrics')
                plans = cur.fetchall()
                assert len(plans) == 1

                maxTimeError = 0.00001
                plan = plans[0]
                assert plan['id'] == 1
                assert plan['inter_tx_jobs'] == 0
                assert plan['domain'] == 'socal.res.rr.com'
                assert plan['data_config'] == 'nonsharedfs'
                assert plan['duration'] == 1.425
                assert plan['clustered_jobs'] == 0
                assert plan['total_jobs'] == 9
                assert plan['remote_addr'] == '104.32.177.85'
                assert plan['compute_jobs'] == 4
                assert plan['hostname'] == 'cpe-104-32-177-85.socal.res.rr.com'
                assert plan['dag_tasks'] == 0
                assert plan['cleanup_jobs'] == 0
                assert plan['application'] is None
                assert plan['version'] == '4.2.0cvs'
                assert plan['create_dir_jobs'] == 1
                assert plan['so_tx_jobs'] == 0
                assert plan['dax_tasks'] == 0
                assert plan['chmod_jobs'] == 0
                assert abs(plan['start_time'] - 1356053279.2479999) < maxTimeError
                assert plan['dag_jobs'] == 0
                assert plan['compute_tasks'] == 4
                assert plan['dax_jobs'] == 0
                assert plan['si_tx_jobs'] == 4
                assert plan['total_tasks'] == 4
                assert plan['wf_uuid'] == '620fe96a-048d-47e8-9000-e8fc347db65e'
                assert plan['root_wf_uuid'] == 'e8a888c1-0e49-4c24-afb1-72d7d5c0ff22'
                assert abs(plan['end_time'] - 1356053280.673) < maxTimeError
                assert plan['reg_jobs'] == 0
                assert plan['exitcode'] == 0


                # Check that the location for the plan was added and that the values are match up with
                # the proper response at the time of writing this (2/2015)
                # If there is an error here it could mean there's a problem calling the service that
                # looks up the location
                cur.execute('select * from locations')
                locations = cur.fetchall()
                assert len(locations) == 1

                maxLatNonError = 0.00001
                location = locations[0]
                assert location['ip'] == '104.32.177.85'
                assert location['country_code'] == 'US'
                assert location['country_name'] == 'United States'
                assert location['region_code'] == 'CA'
                assert location['region_name'] == 'California'
                assert location['city'] == 'Los Angeles'
                assert location['zip_code'] == '90007'
                assert abs(location['latitude'] - 34.027) < maxLatNonError
                assert abs(location['longitude'] + 118.284) < maxLatNonError
                assert location['metro_code'] == '803'


                cur.execute('select count(*) from downloads')
                dlCount = int(cur.fetchone()['count(*)'])
                assert dlCount == 0

                cur.execute('select count(*) from dagman_metrics')
                dagmanCount = int(cur.fetchone()['count(*)'])
                assert dagmanCount == 0

                cur.execute('select count(*) from invalid_data')
                invalidCount = int(cur.fetchone()['count(*)'])
                assert invalidCount == 0

                cur.execute('select count(*) from planner_errors')
                errorCount = int(cur.fetchone()['count(*)'])
                assert errorCount == 0



    def test_top_domains(self):
        # load the mock data
        with open(relfile('addRawData.json'), 'r') as rawDataFile:
            rawData = ast.literal_eval(rawDataFile.read())
            for dataPoint in rawData:
                self.app.post('/metrics', data=dataPoint['data'], headers={'Content-Type' : 'application/json'})

        db.connect(host=app.config["DBHOST"],
                   port=app.config["DBPORT"],
                   user=app.config["DBUSER"],
                   passwd=app.config["DBPASS"],
                   db=app.config["DBNAME"])

        with ctx.db.cursor() as cur:
            rv = self.app.get('/planner/topdomains?start_time=1355952000&end_time=1425168000', headers={'X-Requested-With' : 'XMLHttpRequest'})
            domainData =  ast.literal_eval(rv.data)
            assert domainData['iTotalRecords'] == 1
            record = domainData['aaData'][0]
            assert record['0'] == 'isi.edu' # Domain
            assert record['1'] == '95'      # Workflows
            assert record['2'] == '295,491' # Tasks
            assert record['3'] == '36,375'  # Jobs

if __name__ == '__main__':
    unittest.main()

