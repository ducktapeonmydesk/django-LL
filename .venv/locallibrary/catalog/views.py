from django.contrib.auth.models import User
from django.db.models.base import Model
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.generic.detail import DetailView

# Create your views here.

from .models import Branch, Engine, Service, engineMfg
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
import datetime
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
import simplejson
from rest_framework.parsers import JSONParser
from .serializers import AppointmentSerializer, BranchSerializer
from .models import Appointment, Vehicle, NewAppt
from .forms import EngineForm, AppointmentForm
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.http.response import Http404
from django.views import View
from django.db.models import Q, query

from rest_framework import permissions, status, viewsets, generics
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.generic.list import ListView
from . import serializers, models, utils
from .utils.manage_appointments import execute_helper_functions
from django.contrib.messages.views import SuccessMessageMixin
import datetime as dt
from .utils.email_verification_token import create_unique_token, delete_tokens_if_expired, check_token
from .utils.static_vars import COMPANY_EMAIL_FROM, COMPANY_NAME

def index(request):
    """View function for home page of site"""

    
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': 1,
    }

    # Render the HTML templace index.html with the data in the context variable
    return render(request, 'index.html', context=context)



class CustomerVehiclebyUserView(LoginRequiredMixin, generic.ListView):
    model = Vehicle
    template_name = 'catalog/customer_vehicle_list_user.html'
    paginate_by=25

    def get_queryset(self):
        return Vehicle.objects.filter(sold_to=self.request.user).order_by('unit')

class CustomerVehicleListAll(PermissionRequiredMixin, generic.ListView):
    model = Vehicle
    permission_required = 'catalog.view_all_vehicles'
    template_name = 'catalog/customer_vehicle_list_all.html'
    paginate_by = 25

    def get_queryset(self):
        return Vehicle.objects.order_by('unit')


class EngineCreateView(CreateView):
    model = Engine
    form_class = EngineForm
    #fields = ['engine_model', 'oem', 'servicelevel']

class EngineUpdateView(UpdateView):
    model = Engine
    fields = ['engine_model',  'oem', 'servicelevel']

def load_engines(request):
    engineMfg_id = request.GET.get('engineMfg')
    engines = Engine.objects.filter(engineMfg_id=engineMfg_id).order_by('engines')
    return render(request, 'catalog/engine_dropdown_list_options.html', {'engines': engines})

class engineMfgListView(generic.ListView):
    model = engineMfg
    paginate_by=10

class engineMfgDetailView(generic.DetailView):
    model = engineMfg

class EngineListView(generic.ListView):
    model = Engine
    paginate_by=10

class EngineDetailView(generic.DetailView):
    model = Engine

class VehicleDetailView(generic.DetailView):
    model=Vehicle

class VehicleUpdate(UpdateView):
    model = Vehicle
    fields = ['sold_to', 'unit', 'vin', 'engineMfg', 'mileage']


def new_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(user=request.user, data=request.POST)
        if form.is_valid():
            appt = form.save(commit=False)
            appt.sold_to = request.user
            appt.vin = appt.unit.vin
            appt.servicelevel = appt.unit.engine.servicelevel
            appt.status = 'Requested'
            appt.end_time = appt.start_time + dt.timedelta(hours=2)
            appt.save()
            return redirect('/')
    else:
        form = AppointmentForm(user=request.user)
    return render(request, 'catalog/appointment_form.html', {'form':form})


class AppointmentView(generic.TemplateView):
    template_name = 'template.html'

    def get_context_data(self, **kwargs):
        branch = Branch.objects.all()
        context = super(AppointmentView, self).get_context_data(**kwargs)
        context.update({'branch': branch})
        return context

def get_branch(request, **kwargs):
    branch = Branch.objects.get(id=kwargs['branch_id'])
    branch_list = list(branch.name.values('id', 'name'))

    return HttpResponse(simplejson.dumps(branch_list), context_type='application/json')


class AllBookedAppts(PermissionRequiredMixin, generic.ListView):
    model = NewAppt
    template_name = 'catalog/all_booked_appts.html'
    permission_required = 'catalog.view_all_appts'
    paginate_by=25

    def get_queryset(self):
        return NewAppt.objects.order_by('day')


class CustomerBookedAppts(LoginRequiredMixin, generic.ListView):
    model = NewAppt
    template_name = 'catalog/cust_booked_appts.html'
    paginate_by=25

    def get_queryset(self):
        return NewAppt.objects.order_by('day')


class ApptView(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        queryset = NewAppt.objects.all()
        sold_to = self.request.query_params.get('sold_to')
        if sold_to is not None:
            queryset = queryset.filter(sold_to=self.request.user)
        return queryset


def load_services(request):
    engine_id = request.GET.get('engine')
    services = Service.objects.filter(engine_id=engine_id).order_by('name')
    return render(request, 'catalog/serivce_dropdown_list_options.html', {'services':services})


class NewApptForm(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'catalog/newappt_form.html'

    def get(self, request):
        queryset = NewAppt.objects.all()
        return Response({'appts': queryset})


@api_view(['POST','GET'])
def ApptForm(request):
    form = AppointmentForm(user=request.user, data=request.POST)
    if request.method=='POST':
        serobj = AppointmentSerializer(data=request.POST)
        if serobj.is_valid():
            serobj.save()
            return render(request, 'catalog/cust_booked_appts.html')
            #return Response(serobj.data)
    else:
        form = AppointmentForm(user=request.user)
    return render(request, 'catalog/appointment_form.html', {'form':form})          


class UserSelfView(APIView):
    """
    Get user object with self
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        serializer = serializers.AppUserWithGroupsSerializer(request.user)

        return Response(serializer.data)

class AppointmentsForUserView(APIView):
    """
    Read all appointments for a specific employee_id
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        execute_helper_functions()

        appointments = models.Appointment.objects.filter(Q(employee_id=pk) | Q(customer_id=pk))
        serializer = serializers.AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class PastAppointmentList(APIView):
    """
    Read all appointments
    """
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        execute_helper_functions()

        appointments = models.PastAppointment.objects.all()
        serializer = serializers.PastAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)


class PastAppointmentDetail(APIView):
    """
    Read only functionality for one Appointment
    """
    permission_classes = [permissions.IsAdminUser]

    def _get_appointment(self, pk):
        try:
            return models.PastAppointment.objects.get(pk=pk)
        except models.PastAppointment.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        execute_helper_functions()

        appointment = self._get_appointment(pk)
        serializer = serializers.PastAppointmentSerializer(appointment)
        return Response(serializer.data)


class UsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_name=''):

        if len(group_name) > 0:
                
            try:
                is_valid_group.validate(group_name)
            except ValidationError:#is_valid_group.validate(group_name)
                return Response({'error': f"[{group_name}] is not a valid group."})

            group_name = group_name.lower()
            group_name = group_name[0].upper() + group_name[1:]

            request_user_groups = []
            request_groups_query_set = request.user.groups.all()
            for group in request_groups_query_set:
                request_user_groups.append(group.name)

            users = None
            if (group_name == 'Customers' and 'Customers' in request_user_groups) or \
                (group_name == 'Employees' and 'Employees' in request_user_groups):
                # if it's a customer requesting customers only give them themselves, same with employee requesting employees
                users = [{'id': request.user.id, 'name': request.user.name, 'email': request.user.email, 'phone': request.user.phone}]
                serializer = serializers.AppUserSerializer(users, many=True)

            elif (group_name == 'Customers' and 'Employees' in request_user_groups) or \
                (group_name == 'Employees' and 'Customers' in request_user_groups):
                # if an employee is requesting customers or 
                # if a customer is requesting employees don't include personal info
                users = models.ApiUser.objects.filter(is_active=True).filter(groups__name=group_name)
                serializer = serializers.AppUserNameOnlySerializer(users, many=True)
            else:
                return Response('User not authorized to view this user group', status=status.HTTP_401_UNAUTHORIZED)

        elif request.user.is_staff:
            # admins can view all users
            users = models.ApiUser.objects.filter(is_active=True)
            serializer = serializers.AppUserWithGroupsSerializer(users, many=True)
    
        else:
            return Response('Unauthorized to view this page.')

        return Response(serializer.data)
    

    def post(self, request, group_name=''):
        
        if request.user.is_staff: #permissions.IsAdminUser
            if group_name != '':
                groups_dict = get_or_create_groups()

                serializer = serializers.AppCreateUserSerializer(data=request.data)

                if serializer.is_valid():

                    # make sure a valid group name was passed to the url
                    try:
                        group_name = is_valid_group.validate(group_name)
                    except ValidationError:
                        return Response({'Invalid Group Error': f"[{group_name}] is not a valid group."}, status=status.HTTP_400_BAD_REQUEST)

                    # create new user object
                    new_user = models.ApiUser.objects.create_user(
                        email = serializer.validated_data['email'], 
                        name = serializer.validated_data['name'], 
                        phone = serializer.validated_data['phone'],
                        password = serializer.validated_data['password_submitted']
                    )

                    # add the new user to the appropriate group
                    group = groups_dict[group_name]
                    group.user_set.add(new_user)

                    return Response(status=status.HTTP_201_CREATED)

                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
            else:
                return Response({'error': 'Can only post to /users/<str:group_name>/'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Only admin users can create a new user.'}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # permissions are handled in _get_user()

    def _get_user(self, pk, active_user):
        '''
        This method verifies that the logged in user is the same as
        the one being requested before returning the user object. Or that
        the logged in user is an administrator.
        '''
        error_object = {'error': ''}
        try:
            user = models.ApiUser.objects.get(pk=pk)            
            if user != active_user and active_user.is_staff is False:  # handle permissions
                user = None
                error_object = {'error': 'User is not allowed to view this page.'}
            return user, error_object
        except models.ApiUser.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        user, err = self._get_user(pk, request.user)
        if err['error'] != '':
            return Response(err, status=status.HTTP_403_FORBIDDEN)
        else:
            serializer = serializers.AppUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        '''
        A full user object must be passed:
        {
            "phone": "5555555555",
            "name": "Jesse",
            "password_submitted": "password1"   
        }
        '''

        if 'password_submitted' in request.data.keys():
            
            user, err = self._get_user(pk, request.user)
            if err['error'] != '':
                return Response(err, status=status.HTTP_403_FORBIDDEN)
            else:
                serializer = serializers.AppCreateUserSerializer(user, data=request.data)
                if serializer.is_valid():
                    serializer.save()

                    user, err = self._get_user(pk, request.user)
                    if err['error'] != '':
                        return Response(err, status=status.HTTP_403_FORBIDDEN)
                    else:
                        user.save()
                    return Response(status=status.HTTP_202_ACCEPTED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({'Password not provided error': 'Must provide a password with a user update.'}, status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk):
        # TODO: to delete a user set up delete route 
        #       that doesn't delete but deactivates the user
        #       If it's an employee then make sure to also delete
        #       their schedule
    def delete(self, request, pk):
        user, error = self._get_user(pk, request.user)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmailVerificationTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        delete_tokens_if_expired()

        if request.user.is_staff:
            tokens = models.EmailVerificationToken.objects.all()
            serializer = serializers.EmailVerificationTokenSerializer(tokens, many=True)
            return Response(serializer.data)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request):
        delete_tokens_if_expired()

        try:
            validate_email(request.data['email'])
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

        # Before creating a token associated with an email, first delete any other tokens that might exist
        existing_tokens = models.EmailVerificationToken.objects.filter(email=request.data['email'])
        for token in existing_tokens:
   
            if timezone.now() < token.created + timezone.timedelta(seconds=round(token.keep_alive_seconds / 2, 0)):
                return Response('You can not create another token yet. Try again later.', status=status.HTTP_401_UNAUTHORIZED)

            token.delete()

        token_object = create_unique_token()

        token_serializer = serializers.EmailVerificationTokenSerializer(data={'email': request.data['email'],
                                                                                'key': str(token_object["hash"])})

        if token_serializer.is_valid():
            token_serializer.save()

            try:
                # See if a user matches the email submitted, if so send a link to change password
                models.ApiUser.objects.get(email=request.data['email'])

                subject_suffix = 'Reset Password'
                endpoint = 'reset-password'
                body_init = 'resetting your password'

            except models.ApiUser.DoesNotExist:
                # send email key to create a user if they do not already exist
                subject_suffix = 'Create Account'
                endpoint = 'create-customer'
                body_init = 'creating your account'

            email_from = COMPANY_EMAIL_FROM
            email_to = request.data['email']
            email_subject = f'{COMPANY_NAME} - {subject_suffix}'
            email_body = f'Your verification key:\n\n{token_object["text"][:3]} {token_object["text"][3:]}'

            send_mail(email_subject, email_body, email_from, [email_to], fail_silently=False)

            return Response(f'Verification email sent to {request.data["email"]}', status=status.HTTP_202_ACCEPTED)
        else:
            return Response(token_serializer.errors, status=status.HTTP_417_EXPECTATION_FAILED)    

class CreateCustomerView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, key):
        delete_tokens_if_expired()

        # Must iterate insteat of using .get() because have to check each token
        for token in models.EmailVerificationToken.objects.all():

            if check_token(key, token.key):
                # add the token email into the request.data so it can be validated
                request.data['email'] = token.email

                serializer = serializers.AppCreateUserSerializer(data=request.data)
                if serializer.is_valid():
                    
                    groups_dict = get_or_create_groups()

                    # create new user object
                    new_user = models.ApiUser.objects.create_user(
                        email = serializer.validated_data['email'], 
                        name = serializer.validated_data['name'], 
                        phone = serializer.validated_data['phone'], 
                        password = serializer.validated_data['password_submitted']
                    )

                    # add the new user to the Customers group
                    group = groups_dict['Customers']
                    group.user_set.add(new_user)

                    # remove the token once it's been used
                    token.delete()
                    return Response(status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

        # If it gets here then no tokens matched
        return Response('Invalid link. Try requesting a new link.', status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, key):
        delete_tokens_if_expired()

        # Must iterate insteat of using .get() because have to check each token
        for token in models.EmailVerificationToken.objects.all():

            if check_token(key, token.key):
                
                # find the user associated with the token by email
                user = models.ApiUser.objects.get(email=token.email)
                if user is None:
                    return Response('User not found.', status=status.HTTP_400_BAD_REQUEST)

                # use Django's password validator
                try:
                    validate_password(request.data['password1'], user)
                except ValidationError as e:
                    return Response(e, status=status.HTTP_400_BAD_REQUEST)

                # Make sure the two passwords submitted match
                if request.data['password1'] != request.data['password2']:
                    return Response('Passwords do not match.', status=status.HTTP_406_NOT_ACCEPTABLE)

                # update the user's password
                user.set_password(request.data['password1'])
                user.save()

                # remove the token once it's been used
                token.delete()

                return Response(status=status.HTTP_202_ACCEPTED)

        # If it gets here then no tokens matched
        return Response('Invalid link. Try requesting a new link.', status=status.HTTP_400_BAD_REQUEST)


class HelperSettingsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        helpers = models.HelperSettingsModel.objects.all()
        serializer = serializers.HelperSettingsSerializer(helpers, many=True)
        return Response(serializer.data)


class GroupIdsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        groups = models.GroupIdsModel.objects.all()
        serializer = serializers.GroupIdsSerializer(groups, many=True)
        return Response(serializer.data)

        
class CustomObtainAuthToken(ObtainAuthToken):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = serializers.AuthTokenSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data)
        else:
            return Response(serializer.errors)

class ScheduleList(APIView):
    """
    Read all appointments, or create new appointment
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        schedules = models.EmployeeScheduleModel.objects.all()
        serializer = serializers.EmployeeScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    # only admins and managers can post
    def post(self, request):
        request_user_groups = request.user.groups.all()

        if len(request_user_groups) == 1:
            request_user_group = request_user_groups[0]

            if request_user_group.name in ['Admins', 'Managers']:
                serializer = serializers.EmployeeScheduleSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else: 
                return Response('User not authorized to post a new schedule.')
        else:
            raise Exception(f"User is not a member of exactly one group. {list(request_user_groups)}")


class ScheduleDetail(APIView):
    """
    Read, Update, Delete functionality for one Appointment
    Customers and Employees should only be able to see their own appointments
    """
    permission_classes = [permissions.IsAuthenticated]

    # TODO: only let people change (PUT or DELETE) their own schedules, or admin, or manager

    def _get_schedule(self, pk):
        try:
            return models.EmployeeScheduleModel.objects.get(pk=pk)
        except models.EmployeeScheduleModel.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        schedule = self._get_schedule(pk)
        serializer = serializers.EmployeeScheduleSerializer(schedule)
        return Response(serializer.data)

    def put(self, request, pk):
        schedule = self._get_schedule(pk)
        serializer = serializers.EmployeeScheduleSerializer(schedule, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        schedule = self._get_schedule(pk)
        schedule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MenuList(APIView):
    """
    Read all service items, or create new item
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        schedules = models.ServiceMenuModel.objects.all()
        serializer = serializers.ServiceMenuSerializer(schedules, many=True)
        return Response(serializer.data)

    # only admins and managers can post
    def post(self, request):
        request_user_groups = request.user.groups.all()

        if len(request_user_groups) == 1:
            request_user_group = request_user_groups[0]

            if request_user_group.name in ['Admins', 'Managers']:
                serializer = serializers.ServiceMenuSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else: 
                return Response('User not authorized to add menu item.')
        else:
            raise Exception(f"User is not a member of exactly one group. {list(request_user_groups)}")

class AppointmentList(APIView):
    """
    Read all appointments, or create new appointment
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        execute_helper_functions()
        if request.user.is_staff: # permissions.IsAdminUser
            appointments = models.Appointment.objects.all()
            serializer = serializers.AppointmentSerializer(appointments, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'Unauthorized to view this page.'})

    def post(self, request):
        serializer = serializers.AppointmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print(request.data)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class AppointmentDetail(APIView):
    """
    Read, Update, Delete functionality for one Appointment
    Customers and Employees should only be able to see their own appointments
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_appointment(self, pk):
        try:
            return models.Appointment.objects.get(pk=pk)
        except models.Appointment.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        execute_helper_functions()

        appointment = self._get_appointment(pk)
        serializer = serializers.AppointmentSerializer(appointment)
        return Response(serializer.data)

    def put(self, request, pk):
        appointment = self._get_appointment(pk)
        serializer = serializers.AppointmentSerializer(appointment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        appointment = self._get_appointment(pk)
        appointment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)