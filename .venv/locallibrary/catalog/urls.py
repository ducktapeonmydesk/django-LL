from django.conf.urls import url, re_path
from django.urls import path, include
from django.contrib import admin
from . import views
from .views import *


urlpatterns = [
    path('', views.index, name='index'),
    path('apptform/', views.ApptForm, name='ApptForm'),
    path('ajax/load-engines/', views.load_engines, name='ajax_load_engines'),
    path('add-engine/', views.EngineCreateView.as_view(), name='engine-add'),
    path('engineMfg/', views.engineMfgListView.as_view(), name='engineMfg-list'),
    path('engineMfg/<int:pk>', views.engineMfgDetailView.as_view(), name='engineMfg-detail'),
    path('engines/', views.EngineListView.as_view(), name='engine-list'),
    path('engines/<int:pk>', views.EngineDetailView.as_view(), name='engine-detail'),
    path('all-vehicles/', views.CustomerVehicleListAll.as_view(), name='all-vehicles'),
    path('my-vehicles/', views.CustomerVehiclebyUserView.as_view(), name='my-vehicles'),
    path('vehicles/<pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicle/<pk>/update/', views.VehicleUpdate.as_view(), name='vehicle-update'),
    path('appointment/', views.new_appointment, name='schedule-appt'),
    path('cust-appts/', views.CustomerBookedAppts.as_view(), name='cust-appts'),
    path('all-appts/', views.AllBookedAppts.as_view(), name='all-appts'),
    path('settings/', views.HelperSettingsView.as_view(), name='helper-settings'),
    path('groups/', views.GroupIdsView.as_view(), name='groups'),

    # Users
    path('users/', views.UsersView.as_view(), name='users'),
    path('users/<str:group_name>/', views.UsersView.as_view(), name='users-groups'),
    path('user/self/', views.UserSelfView.as_view(), name="user-self"),
    path('user/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('create-customer/<str:key>/', views.CreateCustomerView.as_view(), name='create-customer'),
    path('reset-password/<str:key>/', views.ResetPasswordView.as_view(), name='reset-password'),
    
    # Appointments
    path('appointments/', views.AppointmentList.as_view(), name='appointment-list'),
    path('appointments/<int:pk>/', views.AppointmentDetail.as_view(), name='appointment-detail'),
    path('appointments-user/<int:pk>/', views.AppointmentsForUserView.as_view(), name='appointment-user'),
    path('past-appointments/', views.PastAppointmentList.as_view(), name='past-appointment-list'),
    path('past-appointment/<int:pk>/', views.PastAppointmentDetail.as_view(), name='past-appointment-detail'),

    # Managers
    path('schedules/', views.ScheduleList.as_view(), name='schedules-list'),
    path('schedule/<int:pk>/', views.ScheduleDetail.as_view(), name='schedule-detail'),
    path('menu/', views.MenuList.as_view(), name='menu-list'),
    # path('menu/<int:pk>/', views..as_view(), name='menu-detail'),

    # Authentication
    path('email-verification-token/', views.EmailVerificationTokenView.as_view(), name='email-token'),
    path('api-token-auth/', views.CustomObtainAuthToken.as_view(), name='api_token_auth'),
]
