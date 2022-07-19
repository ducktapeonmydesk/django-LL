from __future__ import unicode_literals
from enum import unique
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import query
from django.db.models.fields import CharField
from django.db.models.query_utils import Q
from django.urls import reverse
import uuid # req'd for unique instances of a book
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from datetime import date, datetime, timedelta
from django.utils import timezone
import pandas as pd
from django.core.validators import MinLengthValidator, int_list_validator
from .validators import is_int
from django.utils.translation import gettext_lazy as _
from datetime import date
from django import forms
from .managers import CustomUserManager
from .utils.static_vars import EMAIL_VERIFY_TOKEN_KEEP_ALIVE_SECONDS
import redis
from django.conf import settings
import datetime as dt
from .managers import CustomUserManager


# Create your models here.

class ApiUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email'), unique=True, max_length=100, blank=False, null=False)
    name = models.CharField(_('name'), max_length=100, blank=False)
    phone = models.CharField(_('phone number'), max_length=10, unique=True, blank=False, null=False, validators=[MinLengthValidator(10), is_int.validate])
    
    created = models.DateTimeField(auto_now_add=True, auto_created=True)    
    last_appointment_datetime = models.DateTimeField(null=True)
    last_appointment_other_user_id = models.IntegerField(null=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'phone']

    objects = CustomUserManager()

    def __str__(self):
        return self.name

class Branch(models.Model):
    number = models.IntegerField(unique=True,help_text="This is the branch number, such as 1001 for San Antonio")
    name = models.CharField(max_length=100, help_text="This is the branch name, such as San Antonio")

    def __str__(self):
        return str(self.number)

class engineMfg(models.Model):
    name = models.CharField(max_length=100, help_text="This is the Engine Manufacturer, such as Cummins")

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('engineMfg-detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']

class Engine(models.Model):
    engine_model = models.CharField(max_length=100, help_text="This is the engine model, such as ISX 15")
    engineMfg = models.ForeignKey(engineMfg, on_delete=models.SET_NULL, null=True)
    servicelevel = models.ForeignKey('ServiceLevel', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f'{self.engineMfg}, {self.engine_model}'

    def get_absolute_url(self):
        return reverse('engine-detail', args=[str(self.id)])

    class Meta:
        ordering = ['engineMfg', 'engine_model']

class ServiceLevel(models.Model):
    level = models.CharField(max_length=1, help_text="This is the level.  Options are 'G, 1, 2, 3, 4, 5'")
    def __str__(self):
        return self.level

class ServiceType(models.Model):
    type = models.CharField(max_length=20, help_text="This is the service type.  Options are 'Quick Lube, A-Service, B-Service")

    def __str__(self):
        return self.type


class Vehicle(models.Model):
    unit = models.CharField(max_length=10, help_text="Unit number for the vehicle")
    vin = models.CharField(max_length=17, unique=True, validators=[MinLengthValidator(17)],  help_text="VIN of the vehicle", primary_key=True)
    engine = models.ForeignKey(Engine, on_delete=models.SET_NULL, null=True)
    engineMfg = models.ForeignKey(engineMfg, on_delete=models.SET_NULL, null=True)
    sold_to = models.ForeignKey(ApiUser, on_delete=models.SET_NULL, null=True, blank=True)
    #customer = models.ForeignKey(ApiUser, related_name='vehicle_customer', on_delete=models.CASCADE, blank=False, null=False)

    mileage = models.IntegerField(default=0, help_text="Mileage of the vehicle")

    class Meta:
        ordering= ['unit', 'vin']
        permissions = (
            ('view_all_vehicles', "View All Vehicles"), # this is only a permission to do something, it does NOT change a book state
        )
        unique_together = ['sold_to', 'unit']

    def __str__(self):
        return self.unit


class TimeSlot(models.Model):

    Timeslot_List = (
        (0, '7:00am - 09:00am'),
        (1, '09:00am - 11:00am'),
        (2, '1:00pm - 3:00pm'),
        (3, '3:00pm - 5:00pm'),
        (4, '5:00pm - 7:00pm'),
    )

    timeslot = models.IntegerField(choices=Timeslot_List)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.timeslot

class Appointment(models.Model):

    class Meta:
        unique_together = ('branch', 'date', 'timeslots')

    Booking_Status = (
        ('Available', "Available"),
        ('Book', "Booked"),
        ('Requested', "Requested"),
        ('Confirmed', "Confirmed"),
    )

    status = models.CharField(
        max_length=10,
        choices=Booking_Status,
        blank=True,
        default='Available',
        help_text="Booking Availability",
    )


    branch = models.ForeignKey('Branch', on_delete=models.SET_NULL, null=True)
    unit = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    vin = models.CharField(max_length=17)
    date = models.DateField(help_text="MM-DD-YY")
    sold_to = models.ForeignKey(ApiUser, on_delete=models.SET_NULL, null=True)
    timeslots = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True)
    servicetype = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    servicelevel = models.ForeignKey(ServiceLevel, on_delete=models.SET_NULL, null=True) 

 
    def __str__(self):
        return str(self.sold_to)

    @property
    def time(self):
        return self.Timeslot_List[self.timeslots][1]




class BranchSchedule(models.Model):
    """Creates one schedule for each branch"""

    branch = models.OneToOneField(Branch, on_delete=models.CASCADE, primary_key=True)

    holidays = models.CharField(max_length=1000, validators=[int_list_validator], blank=True, null=True) # list of comma separated days [2021-01-01, 2022-12-31]

    monday_first_appt = models.TimeField(blank=False, null=True)
    monday_last_appt = models.TimeField(blank=False, null=True)
    
    tuesday_first_appt = models.TimeField(blank=False, null=True)
    tuesday_last_appt = models.TimeField(blank=False, null=True)

    wednesday_first_appt = models.TimeField(blank=False, null=True)
    wednesday_last_appt = models.TimeField(blank=False, null=True)

    thursday_first_appt = models.TimeField(blank=False, null=True)
    thursday_last_appt = models.TimeField(blank=False, null=True)

    friday_first_appt = models.TimeField(blank=False, null=True)
    friday_last_appt = models.TimeField(blank=False, null=True)

    saturday_first_appt = models.TimeField(blank=False, null=True)
    saturday_last_appt = models.TimeField(blank=False, null=True)
    


class HelperSettingsModel(models.Model):
    last_appt_cleanup_time = models.DateTimeField(default=timezone.datetime(2000, 1, 1 , 0, 0, 0))


class GroupIdsModel(models.Model):
    group_id = models.IntegerField(null=True)
    group_name = models.CharField(max_length=100, blank=False, null=False)


class ServiceMenuModel(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    category = models.CharField(max_length=100, blank=False, null=False)
    price = models.FloatField(blank=False, null=False)
    time_minutes = models.IntegerField(blank=False, null=False)



class Service(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)
    service_type = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    service_level = models.ForeignKey(ServiceLevel, on_delete=models.SET_NULL, null=True)
    price = models.FloatField(blank=False, null=False)
    #time_minutes = models.IntegerField(blank=False, null=False)
    duration = models.DurationField(null=True, default=timedelta(minutes=60), help_text="HH:MM:SS")
    laborop = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class AvailDates(models.Model):
    day = models.DateField(null=True)

    def __str__(self):
        return self.day

class AvailTimes(models.Model):
    time = models.TimeField(default=dt.time(00, 00))
    day = models.ForeignKey(AvailDates, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return self.begin_time


class NewAppt(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    day = models.DateField(null=True)
    begin_time = models.TimeField(null=True)
    start_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    unit = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    vin = models.CharField(max_length=17)
    #vin = models.ForeignKey(Vehicle, related_name='VIN', on_delete=models.SET_NULL, null=True)
    sold_to = models.ForeignKey(ApiUser, on_delete=models.SET_NULL, null=True)
    servicelevel = models.ForeignKey(ServiceLevel, on_delete=models.SET_NULL, null=True)
    servicetype = models.ForeignKey(ServiceType, on_delete=models.SET_NULL, null=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    duration = models.DurationField()

    def __str__(self):
        return f'{self.branch} | StartTime = {self.start_time} | EndTime = {self.end_time} | SoldTo = {self.sold_to} | Service = {self.servicetype} | Level = {self.servicelevel}'

    class Meta:
        ordering = ['branch', 'start_time']
        unique_together = ('branch', 'start_time')

    def save(self, **kwargs):
        self.vin = self.unit.vin
        #self.vin = Vehicle.objects.get(unit=self.unit)
        self.sold_to=self.unit.sold_to
        self.servicelevel = self.unit.engine.servicelevel
        self.service = Service.objects.get(service_level=self.servicelevel, service_type=self.servicetype)
        self.start_time = datetime.combine(self.day, self.begin_time)
        self.duration = self.service.duration
        self.end_time = self.start_time + self.duration
        super().save(**kwargs)


class PastAppt(models.Model):
    created = models.DateTimeField(blank=False, null=True)
    start_time = models.DateTimeField(blank=False)
    end_time = models.DateTimeField(blank=False)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    unit = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True)
    vin = models.CharField(max_length=17)
    sold_to = models.ForeignKey(ApiUser, on_delete=models.SET_NULL, null=True)
    services = models.CharField(max_length=1000, validators=[int_list_validator], blank=False, null=False) # list of comma separated service id's [1, 2, 6]

    def __str__(self):
        return f'{self.Branch} | StartTime={self.start_time} | EndTime={self.end_time} | SoldTo={self.sold_to} | Service{self.services}'

    class Meta:
        ordering = ['branch', 'start_time']


class EmailVerificationToken(models.Model):
    email = models.EmailField(blank=False, null=False, unique=True)
    key = models.CharField(max_length=200, unique=True) # can set default=some_key_gen_method to auto generate the key
    created = models.DateTimeField(auto_now_add=True)
    keep_alive_seconds = models.IntegerField(default=EMAIL_VERIFY_TOKEN_KEEP_ALIVE_SECONDS)
