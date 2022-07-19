from django.contrib import admin
from django.contrib.admin.helpers import Fieldset
from django.contrib.auth.models import User
from django.core.exceptions import ViewDoesNotExist
from django.contrib.auth.admin import UserAdmin

from .forms import ApiUserChangeForm, ApiUserCreationForm
#from .forms import ApiUserCreationForm, ApiUserChangeForm

# Register your models here.

from .models import BranchSchedule, Service, engineMfg, ServiceLevel, ServiceType, Engine, Vehicle, Appointment, Branch, NewAppt, ApiUser

_ = admin.site.register

class CustomUserAdmin(UserAdmin):
    add_form = ApiUserCreationForm
    form = ApiUserChangeForm
    model = ApiUser


class VehicleAdmin(admin.ModelAdmin):
    list_dispaly=('vin', 'oem', 'unit', 'engine')


class AppointmentAdmin(admin.ModelAdmin):

    list_display = ('branch', 'date', 'timeslots', 'sold_to', 'unit', 'VIN', 'vin')
    list_filter = ('branch', 'date', 'sold_to', 'unit', 'vin')

    def VIN(self, obj):
        return obj.unit.vin

class NewApptAdmin(admin.ModelAdmin):
    list_display = ('branch', 'sold_to', 'start_time', 'servicetype', 'servicelevel', 'vin', 'unit')
    list_filter = ('branch', 'sold_to', 'start_time', 'servicetype', 'servicelevel', 'vin', 'unit')


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_level', 'service_type', 'price', 'duration')

class BranchScheduleAdmin(admin.ModelAdmin):
    list_display = ('branch', 'monday_first_appt',  'monday_last_appt', 'saturday_first_appt', 'saturday_last_appt')


_(engineMfg)
_(ServiceType)
_(ServiceLevel)
_(Engine)
_(Vehicle, VehicleAdmin)
_(Appointment, AppointmentAdmin)
_(Branch)
_(NewAppt, NewApptAdmin)
_(Service, ServiceAdmin)
_(BranchSchedule, BranchScheduleAdmin)
