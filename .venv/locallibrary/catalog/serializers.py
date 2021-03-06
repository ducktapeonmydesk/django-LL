import datetime
from django.contrib.auth.models import User
from django.db.models.fields import IntegerField
from rest_framework import fields, serializers
from rest_framework.authtoken.models import Token
from rest_framework import exceptions
from catalog.models import *
from catalog.validators import appt_fits_branch_schedule, prevent_double_book, is_valid_password, is_valid_group
from django.contrib.auth import authenticate

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


class GroupIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupIdsModel
        fields = '__all__'


class AppUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiUser
        fields = ['id', 'email', 'name', 'phone']

class AppUserNameOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiUser
        fields = ['id', 'name']

class AppUserEmailAndPhoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiUser
        fields = ['id', 'email', 'phone']


class AppUserWithGroupsSerializer(serializers.ModelSerializer):

    class Meta:
        model = ApiUser
        fields = ['id', 'email', 'phone', 'name', 'groups']


class AppCreateUserSerializer(serializers.ModelSerializer):
    password_submitted = serializers.CharField(max_length=100, validators=[is_valid_password.validate])

    class Meta:
        model = ApiUser
        fields = ['id', 'email', 'name', 'phone', 'password_submitted']


class AppUserChangePasswordSerializer(serializers.ModelSerializer):
    password_submitted = serializers.CharField(max_length=100, validators=[is_valid_password.validate])

    class Meta:
        model = ApiUser
        fields = ['id', 'email', 'password_submitted']


class ServiceMenuSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceMenuModel
        fields = '__all__'

class EmployeeScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BranchSchedule
        fields = '__all__'


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, max_length=100)
    password = serializers.CharField(required=True, max_length=100)

    def validate(self, data):
        email = data.get('email', None)
        password = data.get('password', None)

        user = authenticate(username=email, password=password)

        if user is None:
            raise exceptions.AuthenticationFailed('Incorrect email and/or password.')
        else:
            token, _ = Token.objects.get_or_create(user=user)
            return {
                'token': token.key
            }

class EmailVerificationTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerificationToken
        fields = '__all__'