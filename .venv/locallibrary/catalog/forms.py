from django import forms
import datetime
from datetime import date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import fields
from django.forms import widgets
from django.forms.widgets import DateTimeBaseInput
from django.utils.translation import ugettext_lazy as _
from .models import Appointment, Engine, NewAppt, Vehicle, engineMfg, ServiceLevel, ServiceType
import json
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from catalog.validators import appt_fits_branch_schedule, prevent_double_book
import datetime as dt
from django.contrib.admin.widgets import AdminDateWidget
from django.forms.fields import DateField


class EngineForm(forms.ModelForm):
    class Meta:
        model = Engine
        fields = ('engineMfg', 'engine_model')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['engine_model'].queryset = Engine.objects.none()


hour_choices = [(dt.time(hour=x), '{:02d}:00'.format(x)) for x in range(7,17)]

class AppointmentForm(forms.ModelForm):

    class Meta:
        model = NewAppt
        exclude = ('status', 'sold_to', 'vin', 'servicelevel', 'end_time', 'service', 'duration', 'start_time')
        widgets = {'begin_time': forms.Select(choices=hour_choices)}
        '''
        widgets = {
            'start_time': DateTimeWidget(
                attrs={'id': 'start_time'}, usel10n=True, bootstrap_version=4,
                options={
                    'minView': 2, # month view
                    'maxView': 3, # year view
                    'weekStart': 1,
                    'todayHighlight': True,
                    'format': 'mm-dd-yy',
                    'daysOfWeekDisabled': [0,6],
                    'startDate': date.today().strftime('%Y-%m-%d'),
                }
            ),
        }
        '''


    def clean_date(self):
        day = self.cleaned_data['day']

        if day <= date.today():
            raise forms.ValidationError("Date should be in the future", code='invalid')
        if day.isoweekday() in (0,6):
            raise forms.ValidationError("Must be scheduled on a weekday", code='invalid')

        return day

    #
    #def combine_date_time(self):
    #    day = self.cleaned_data['day']
    #    time = self.cleaned_data['begin_time']
    #    start_time = datetime.combine(day, time)
    #    return start_time

    
    def check_conflicts(self):
        starttime = self.cleaned_data['start_time']
        endtime = starttime+datetime.timedelta(hours=2)

        start_conflict = NewAppt.objects.filter(startime__range=(starttime, endtime))
        end_conflict = NewAppt.objects.filter(endtime_range=(starttime, endtime))
        during_conflict = NewAppt.objects.filter(startdate__lte=starttime,end_date__gte=endtime)
        if (start_conflict or end_conflict or during_conflict):
            raise forms.ValidationError("There is already an appointment scheduled during this time.")
        return starttime, endtime
    
    def __init__(self, **kwargs):
        sold_to = kwargs.pop('user')
        super(AppointmentForm, self).__init__(**kwargs)
        self.fields['unit'].queryset = Vehicle.objects.filter(sold_to=sold_to)
        #self.fields['timeslot'].queryset = TimeSlot.objects.none()
        
        #if 'date' in self.data:
         #   try:
          #      date_id = int(self.data.get('appointment'))
           #     self.fields['timeslot'].queryset = TimeSlot.objects.filter()



class NewApptForm(forms.ModelForm):
    class Meta:
        model = NewAppt
        fields = {'branch', 'unit'}
