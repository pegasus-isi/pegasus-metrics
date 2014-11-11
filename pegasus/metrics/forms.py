import time
from flask import session
from wtforms import Form, SelectField

class PeriodForm(Form):
    period = SelectField(choices=[
        ('day', 'the last day'), 
        ('week', 'the last week'),
        ('month', 'the last month'),
        ('year', 'the last year'),
        ('all time', 'all time')
    ])
    
    def __init__(self, *args, **kwargs):
        
        kwargs["period"] = session.get("period", "week")
        
        Form.__init__(self, *args, **kwargs)
    
    def validate_period(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid period '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

        session["period"] = field.data
        
    def get_start(self):
        DAY = 24*60*60
        WEEK = 7*DAY
        MONTH = 30*DAY # Close enough
        YEAR = 365*DAY
        
        period = self.period.data
        
        if period is None or period == "None":
            period = "week"
        
        now = time.time()
        
        if period == "day":
            start = now - DAY
        elif period == "week":
            start = now - WEEK
        elif period == "month":
            start = now - MONTH
        elif period == "year":
            start = now - YEAR
        elif period == "all time":
            start = 0
        else:
            raise Exception("Invalid period: %s" % period)
        
        return start

    def get_end(self):
        return time.time()

class LimitForm(Form):
    limit = SelectField(choices=[
        ('50', '50'),
        ('100','100'),
        ('200', '200'),
        ('all', 'all')
    ])

    def __init__(self, *args, **kwargs):
        kwargs['limit'] = session.get('limit', 50)
        Form.__init__(self, *args, **kwargs)

    def validate_limit(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid limit '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

        session["limit"] = field.data

    def get_limit(self):
        limit = self.limit.data
        if limit is None or limit == "None":
            limit = 50
        return limit

class MapForm(Form):
    pins = SelectField(choices=[
        ('hostname', 'Top Hosts'),
        ('domain', 'Top Domains'),
        ('recent_planner_metrics', 'Recent Runs'),
        ('recent_downloads', 'Recent Downloads'),
        ('downloads', 'Top Downloads')
    ])

    limit = SelectField(choices=[
        ('50', '50'),
        ('100','100'),
        ('200', '200'),
        ('all', 'all')
    ])

    def __init__(self, *args, **kwargs):
        kwargs['limit'] = session.get('limit', 50)
        kwargs['pins'] = session.get('pins', 'domain')
        print kwargs['pins']
        Form.__init__(self, *args, **kwargs)

    def validate_limit(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid limit '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

        session["limit"] = field.data

    def validate_pins(selfself, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid pins '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

    def get_limit(self):
        limit = self.limit.data
        if limit is None or limit == "None":
            limit = 50
        return limit

    def get_pins(self):
        pins = self.pins.data
        if pins is None or pins == "None":
            pins = 'domain'
        return pins