from django.conf.urls import url, re_path
from django.urls import path, include
from django.contrib import admin
from . import views


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
]
