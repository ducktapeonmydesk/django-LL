from asgiref.sync import sync_to_async
from django.utils import timezone
from ..models import NewAppt, PastAppt, HelperSettingsModel, BranchSchedule
from ..serializers import AppointmentSerializer, PastAppointmentSerializer, BranchScheduleSerializer, HelperSettingsSerializer



def _move_complete_appointmentsa_to_past_appointments():
    appointments = NewAppt.objects.all()
    for appointment in appointments:
        if timezone.now() > appointment.end_time:

            past_appointment_object = {
                'appointment_id': appointment.id,
                'start_time': appointment.start_time,
                'end_time': appointment.end_time,
                'sold_to': appointment.sold_to,
                'branch': appointment.branch,
                'created': appointment.created,
                'services': appointment.services,
                'vin': appointment.vin,
                'unit': appointment.unit,
            }

            print('\n\nPAST APPT:\n', past_appointment_object, '\n\n')

            past_appointment_serializer = PastAppointmentSerializer(data=past_appointment_object)

            # save past appointments to PastAppointsments and remove them from Appointments
            if past_appointment_serializer.is_valid():
                print('\n\nAPPT TO DELETE:\n', appointment, '\n\n')
                past_appointment_serializer.save()
                appointment.delete()
            else:
                print(f'\nERROR SERIALIZING DATA: {past_appointment_serializer.errors}\n')

def _instatiate_helper_model():
    helper_object = {
        'last_appt_cleanup_time': timezone.now() - timezone.timedelta(days=30)
    }
    helper_serializer = HelperSettingsSerializer(data=helper_object)

    if helper_serializer.is_valid():
        helper_serializer.save()
    else:
        raise Exception(f'\nERROR INSTATIATING HELPER MODEL: {helper_serializer.errors}\n')


def _create_helper_object_if_not_exists():
    helpers = HelperSettingsModel.objects.all()

    if len(helpers) == 0:
        _instatiate_helper_model()
    else:
        for helper in helpers:
            if helper.id != 1:
                helper.delete()
    
        if len(helpers) == 0:
            _instatiate_helper_model()


def _delete_old_appt():
    helper_object = HelperSettingsModel.objects.get(pk=1)
    last_update = helper_object.last_appointment_cleanup_time

    cutoff_datetime = last_update + timezone.timedelta(days=365)

    if timezone.now() > cutoff_datetime:

        past_appointments = PastAppt.objects.order_by('start_time')[:1000]

        cutoff_datetime = timezone.now() - timezone.timedelta(days = 365)

        for appointment in past_appointments:
            if appointment.end_time < cutoff_datetime or appointment.start_time < cutoff_datetime:
                appointment.delete()
        
        helper_serializer = HelperSettingsSerializer(helper_object, {'lsat_appointment_cleanup_time': timezone.now()}, partial=True)
        helper_serializer.is_valid(raise_exception=True)
        helper_serializer.save()

def execute_helper_functions():
    _create_helper_object_if_not_exists()
    _move_complete_appointmentsa_to_past_appointments()
    #sync_to_async(_delete_old_appt(), thread_sensitive=True)
