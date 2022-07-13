import datetime
from django.contrib.auth.models import User
from django.db.models.fields import IntegerField
from rest_framework import fields, serializers
from rest_framework.authtoken.models import Token
from rest_framework import exceptions
from catalog.models import NewAppt, PastAppt, Branch, Service, HelperSettingsModel, BranchSchedule, Vehicle, Engine
from catalog.validators import appt_fits_branch_schedule, prevent_double_book, is_valid_password, is_valid_group

class VINSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('vin',)

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class EngineLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = ('servicelevel',)



class AppointmentSerializer(serializers.ModelSerializer):


    def validate(self, appointment):
        appointment = appt_fits_branch_schedule.validate(appointment)
        appointment = prevent_double_book.validate(appointment)
        return appointment

    

    class Meta:
        model = NewAppt
        fields = ('branch', 'sold_to', 'start_time', 'end_time', 'unit', 'vin', 'servicetype', 'servicelevel', 'duration', 'begin_time', 'day')
        read_only_fields = ('end_time', 'vin', 'sold_to', 'servicelevel', 'duration', 'start_time')




class PastAppointmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = PastAppt
        fields = '__all__'


class HelperSettingsSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = HelperSettingsModel
        fields = '__all__'


class BranchSerializer(serializers.ModelSerializer):
    #appointment_set = AppointmentSerializer(many=True, read_only=True)

    class Meta:
        model = Branch
        fields = ('number', 'name')


class BranchScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = BranchSchedule
        fields = '__all__'




