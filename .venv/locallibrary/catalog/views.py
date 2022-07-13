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
from catalog.serializers import AppointmentSerializer, BranchSerializer
from catalog.models import Appointment, Vehicle, NewAppt
from catalog.forms import EngineForm, AppointmentForm
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
from catalog import serializers, models
from catalog.utils.manage_appointments import execute_helper_functions
from django.contrib.messages.views import SuccessMessageMixin
import datetime as dt

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


