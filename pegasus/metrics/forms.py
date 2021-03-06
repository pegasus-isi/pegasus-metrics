import time
import datetime
from flask import session
from wtforms import Form, SelectField, IntegerField

epoch = datetime.date(1970,1,1)
daysToSeconds = 24 * 60 * 60

def getStartTime(year,month):
    start = datetime.date(year, month, 1)
    return (start - epoch).days * daysToSeconds

def getEndTime(year, month):
    month = month + 1
    if month == 13:
        month = 1
        year = year + 1
    end = datetime.date(year, month, 1)
    return (end - epoch).days * daysToSeconds

class PeriodForm(Form):

    monthsOfYear = [
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
    ]

    yearsFrom2012ToNow = [(year,year) for year in range(2012, datetime.date.today().year+1)]

    monthStart = SelectField(choices=monthsOfYear)
    yearStart = SelectField(choices= yearsFrom2012ToNow)

    monthEnd = SelectField(choices=monthsOfYear)
    yearEnd = SelectField(choices=yearsFrom2012ToNow)
    
    def __init__(self, *args, **kwargs):
        today = datetime.date.today()
        kwargs["monthEnd"] = session.get("monthEnd", today.month)
        kwargs["yearEnd"] = session.get("yearEnd", today.year)

        lastMonth = today - datetime.timedelta(days=30)
        kwargs["monthStart"] = session.get("monthStart", lastMonth.month)
        kwargs["yearStart"] = session.get("yearStart", lastMonth.year)
        
        Form.__init__(self, *args, **kwargs)


    def general_validate_month(self, field):
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

    def general_validate_year(self, field):
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

    def validate_monthStart(self, field):
        self.general_validate_month(field)

    def validate_yearStart(self, field):
        self.general_validate_year(field)

    def validate_monthEnd(self, field):
        self.general_validate_month(field)

    def validate_yearEnd(self, field):
        self.general_validate_year(field)

    def get_start(self):
        return getStartTime(int(self.yearStart.data), int(self.monthStart.data))

    def get_end(self):
        return getEndTime(int(self.yearEnd.data), int(self.monthEnd.data))

class MapForm(PeriodForm):
    pins = SelectField(choices=[
        ('hostname', 'Top Planner Hosts'),
        ('recent_planner_metrics', 'Recent Plans'),
        ('recent_downloads', 'Recent Downloads')
    ])

    def __init__(self, *args, **kwargs):
        kwargs['pins'] = session.get('pins', 'hostname')
        PeriodForm.__init__(self, *args, **kwargs)

    def validate_pins(self, field):
        valid = [choice[0] for choice in field.choices]
        if field.data not in valid:
            invalid = field.data
            field.data = field.default
            field.errors = []
            field.errors.append("Invalid pins '%s'" % invalid)
            field.errors.append("Using '%s' instead" % field.default)

    def get_pins(self):
        pins = self.pins.data
        if pins is None or pins == "None":
            pins = 'hostname'
        return pins

class TrendForm(PeriodForm):
    def __init__(self, *args, **kwargs):
        PeriodForm.__init__(self, *args, **kwargs)

    def get_monthly_intervals(self):
        monthlyIntervals = [self.get_end()]

        endYear = int(self.yearEnd.data)
        endMonth = int(self.monthEnd.data)
        while getStartTime(endYear,endMonth) > self.get_start():
            monthlyIntervals.append(getStartTime(endYear,endMonth))

            endMonth = endMonth - 1
            if endMonth == 0:
                endMonth = 12
                endYear = endYear - 1
        monthlyIntervals.append(self.get_start())

        return monthlyIntervals

class HistogramForm(PeriodForm):

    jobOrFile = SelectField(choices=[
        ('job', 'Job'),
        ('file', 'File')
    ])

    fileType = SelectField(choices=[
        ('dax_input_files', 'DAX Input Files'),
        ('dax_inter_files', 'DAX Inter Files'),
        ('dax_output_files', 'DAX Output Files'),
        ('dax_total_files', 'DAX Total Files')
    ])

    jobType = SelectField(choices=[
        ('chmod_jobs', 'Chmod Jobs'),
        ('inter_tx_jobs', 'Inner TX Jobs'),
        ('compute_jobs', 'Compute Jobs'),
        ('cleanup_jobs', 'Cleanup Jobs'),
        ('dax_jobs', 'DAX Jobs'),
        ('dag_jobs', 'DAG Jobs'),
        ('so_tx_jobs', 'SO TX Jobs'),
        ('si_tx_jobs', 'SI TX Jobs'),
        ('create_dir_jobs', 'Create Dir Jobs'),
        ('clustered_jobs', 'Clustered Jobs'),
        ('reg_jobs', 'REG Jobs'),
        ('total_jobs', 'Total Jobs')
    ])

    min = IntegerField()
    max = IntegerField()

    def __init__(self, *args, **kwargs):
        kwargs['min'] = 0
        kwargs['max'] = 1000
        kwargs['jobOrFile'] = session.get('jobOrFile', 'job')
        kwargs['jobType'] = session.get('jobType', 'total_jobs')
        kwargs['fileType'] = session.get('fileType', 'dax_total_files')

        PeriodForm.__init__(self, *args, **kwargs)

    def get_intervals(self):
        intervalCount = 10 #Change this to change hoe many bars we want
        intervalDifference = (self.max.data - self.min.data) / intervalCount
        intervals = []
        for i in range(self.min.data, self.max.data, intervalDifference):
            intervals.append(i)
        intervals.append(self.max.data)
        return intervals

    def get_metric(self):
        if self.jobOrFile.data == 'job':
            return self.jobType.data
        return self.fileType.data

    def get_min(self):
        return self.min.data

    def get_max(self):
        return self.max.data