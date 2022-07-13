from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import pytz
from django.conf import settings
from catalog.models import NewAppt

def validate(appointment):

    start_date_time = datetime.combine(appointment['day'], appointment['begin_time'])
    
    server_timezone = pytz.timezone(settings.TIME_ZONE)

    #appointment_start_datetime_tz = appointment['start_time'].astimezone(server_timezone)
    appointment_start_datetime_tz = start_date_time.astimezone(server_timezone)
    #appointment_end_datetime_tz =  appointment['end_time'].astimezone(server_timezone)
    appointment_end_datetime_tz =  appointment_start_datetime_tz + timedelta(hours=2)

    appointment_start_time_tz = appointment_start_datetime_tz.time()
    appointment_end_time_tz = appointment_end_datetime_tz.time()

    #appointment_date_utc = appointment['start_time'].astimezone(pytz.utc).date() # convert to UTC to compare with server
    appointment_date_utc = start_date_time.astimezone(pytz.utc).date()
    appointments_for_date = NewAppt.objects.filter(start_time__date=appointment_date_utc)

    for existing_appointment in appointments_for_date:
        
        existing_appointment.start_time = existing_appointment.start_time.astimezone(server_timezone).time()
        existing_appointment.end_time = existing_appointment.end_time.astimezone(server_timezone).time()

        branch_is_same = appointment['branch'] == existing_appointment.branch

        error = False
        if branch_is_same and appointment_start_time_tz < existing_appointment.start_time and appointment_end_time_tz > existing_appointment.end_time:
            error = True
        
        elif branch_is_same and appointment_start_time_tz < existing_appointment.end_time and appointment_end_time_tz > existing_appointment.end_time:
            error = True
        
        elif branch_is_same and appointment_start_time_tz >= existing_appointment.start_time and appointment_end_time_tz <= existing_appointment.end_time:
            error = True
            

        if error:
            appointment_string = f'[ {appointment_start_time_tz} - {appointment_end_time_tz} ]'
            existing_appointment_string = f'[ {existing_appointment.start_time} - {existing_appointment.end_time} ]'
            raise ValidationError( 'Appointment %(appointment)s overlaps with the existing appoint %(existing_appointment)s',
                                    params={'appointment': appointment_string, 'existing_appointment': existing_appointment_string})
   

    if appointment_start_datetime_tz > appointment_end_datetime_tz:
        error = True
        raise ValidationError('Appointment start date is after appointment end date')
    if appointment_start_time_tz > appointment_end_time_tz and appointment_start_datetime_tz > appointment_end_datetime_tz:
        error = True
        raise ValidationError('Appointment start time is after appointment end time')
            
    return appointment