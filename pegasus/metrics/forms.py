import time
import datetime
from flask import session
from wtforms import Form, SelectField, IntegerField

class PeriodForm(Form):

    monthStart = SelectField(choices=[
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ])
    yearStart = SelectField(choices=[(year,year) for year in range(2012, datetime.date.today().year+1)])

    monthEnd = SelectField(choices=[
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ])
    yearEnd = SelectField(choices=[(year,year) for year in range(2012, datetime.date.today().year+1)])
    
    def __init__(self, *args, **kwargs):
        today = datetime.date.today()
        kwargs["monthEnd"] = session.get("monthEnd", today.month)
        kwargs["yearEnd"] = session.get("yearEnd", today.year)

        lastMonth = today - datetime.timedelta(days=30)
        kwargs["monthStart"] = session.get("monthStart", lastMonth.month)
        kwargs["yearStart"] = session.get("yearStart", lastMonth.year)
        #print self.yearStart.data
        
        Form.__init__(self, *args, **kwargs)


    def validate_monthStart(self, field):
        try:
            month = int(field.data)
            if month > 12 or month < 1:
                field.data = field.default
                field.errors.append("Month must be between 1 and 12")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Month must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_yearStart(self, field):
        try:
            year = int(field.data)
            if year > datetime.date.today().year or year < 2012:
                field.data = field.default
                field.errors.append("The year must be between the epoch and now")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Year must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_monthEnd(self, field):
        try:
            month = int(field.data)
            if month > 12 or month < 1:
                field.data = field.default
                field.errors.append("Month must be between 1 and 12")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Month must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_yearEnd(self, field):
        try:
            year = int(field.data)
            if year > datetime.date.today().year or year < 2012:
                field.data = field.default
                field.errors.append("The year must be between the epoch and now")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Year must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def get_start(self):
        startDate = datetime.date(int(self.yearStart.data), int(self.monthStart.data), 1)
        return (startDate - datetime.date(1970,1,1)).days * 24 * 60 * 60


    def get_end(self):
        year = int(self.yearEnd.data)
        month = int(self.monthEnd.data) + 1
        if month == 13:
            month = 1
            year = year + 1
        endDate = datetime.date(int(year), int(month), 1)
        return (endDate - datetime.date(1970,1,1)).days * 24 * 60 * 60

# We might not need this form anymore, but just in case it'll remain in the code to prevent
# any surprise errors from occurring
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

    monthStart = SelectField(choices=[
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ])
    yearStart = SelectField(choices=[(year,year) for year in range(2012, datetime.date.today().year+1)])

    monthEnd = SelectField(choices=[
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ])
    yearEnd = SelectField(choices=[(year,year) for year in range(2012, datetime.date.today().year+1)])

    def __init__(self, *args, **kwargs):
        kwargs['pins'] = session.get('pins', 'domain')

        today = datetime.date.today()
        kwargs["monthEnd"] = session.get("monthEnd", today.month)
        kwargs["yearEnd"] = session.get("yearEnd", today.year)

        lastMonth = today - datetime.timedelta(days=30)
        kwargs["monthStart"] = session.get("monthStart", lastMonth.month)
        kwargs["yearStart"] = session.get("yearStart", lastMonth.year)

        Form.__init__(self, *args, **kwargs)

    def validate_pins(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid pins '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

    def validate_monthStart(self, field):
        try:
            month = int(field.data)
            if month > 12 or month < 1:
                field.data = field.default
                field.errors.append("Month must be between 1 and 12")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Month must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_yearStart(self, field):
        try:
            year = int(field.data)
            if year > datetime.date.today().year or year < 1970:
                field.data = field.default
                field.errors.append("The year must be between the epoch and now")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Year must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_monthEnd(self, field):
        try:
            month = int(field.data)
            if month > 12 or month < 1:
                field.data = field.default
                field.errors.append("Month must be between 1 and 12")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Month must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def validate_yearEnd(self, field):
        try:
            year = int(field.data)
            if year > datetime.date.today().year or year < 1970:
                field.data = field.default
                field.errors.append("The year must be between the epoch and now")
                field.errors.append("Using '%s' instead" % field.default)
        except ValueError:
            field.data = field.default
            field.errors.append("Year must be an integer value")
            field.errors.append("Using '%s' instead" % field.default)

    def get_start(self):
        startDate = datetime.date(int(self.yearStart.data), int(self.monthStart.data), datetime.date.today().day)
        return (startDate - datetime.date(1970,1,1)).days * 24 * 60 * 60


    def get_end(self):
        year = int(self.yearEnd.data)
        month = int(self.monthEnd.data) + 1
        if month == 13:
            month = 1
            year = year + 1
        endDate = datetime.date(int(year), int(month), 1)
        return (endDate - datetime.date(1970,1,1)).days * 24 * 60 * 60

    def get_pins(self):
        pins = self.pins.data
        if pins is None or pins == "None":
            pins = 'domain'
        return pins

class TrendForm(Form):
    trend = SelectField(choices=[
        ('3', 'Last Three Months'),
        ('6', 'Last Six Months'),
        ('12', 'Last Year')
    ])

    def __init__(self, *args, **kwargs):
        kwargs['trend'] = session.get('trend', '3')

        Form.__init__(self, *args, **kwargs)

    def validate_trend(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid trend '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

        session["trend"] = field.data

    def get_monthly_intervals(self):
        today = datetime.date.today()

        endYear = today.year
        endMonth = today.month + 1
        if endMonth == 13:
            endMonth = 1
            endYear = endYear + 1

        monthlyIntervals = [datetime.date(endYear, endMonth, 1) - datetime.date(1970,1,1).days * 24 * 60 * 60]

        trend = int(self.trend.data)


        for i in range(trend):
            endMonth = endMonth - 1
            if endMonth == 0:
                endMonth = 12
                endYear = endYear - 1
            monthlyIntervals.append(datetime.date(endYear, endMonth, 1) - datetime.date(1970,1,1).days * 24 * 60 * 60)

        return monthlyIntervals

    def get_start(self):
        today = datetime.date.today()

        trend = int(self.trend.data)
        if trend is None or trend == "None":
            trend = 3

        startYear = today.year
        startMonth = today.month - trend
        if startMonth < 1:
            startMonth = startMonth + 12
            startYear = startYear - 1


        return datetime.date(startYear, startMonth, 1) - datetime.date(1970,1,1).days * 24 * 60 * 60

    def get_end(self):
        today = datetime.date.today()

        endYear = today.year
        endMonth = today.month + 1
        if endMonth == 13:
            endMonth = 1
            endYear = endYear + 1
        return datetime.date(endYear, endMonth, 1) - datetime.date(1970,1,1).days * 24 * 60 * 60

