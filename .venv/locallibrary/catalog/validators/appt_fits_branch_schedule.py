from datetime import datetime
from django.core.exceptions import ValidationError
import pytz
from django.conf import settings
from catalog.models import BranchSchedule

SERVER_TIMEZONE = pytz.timezone(settings.TIME_ZONE)

def _localize_date_string(date_string):
    if date_string:
        return SERVER_TIMEZONE.localize(datetime.strptime(str(date_string), "%Y-%m-%d")).date()
    else:
        return None

def validate(appointment):
    timezone_to_use = SERVER_TIMEZONE

    start_date_time = datetime.combine(appointment['day'], appointment['begin_time'])

    #appointment_start_datetime = appointment['start_time'].astimezone(timezone_to_use)
    appointment_start_datetime = start_date_time.astimezone(timezone_to_use)
    appointment_start_time = appointment_start_datetime.time()
    appointment_weekday = appointment_start_datetime.weekday()
    appointment_date = appointment_start_datetime.date()

    error = False
    branch_schedule = BranchSchedule.objects.get(pk=appointment['branch'])
    if branch_schedule:

        #convert holiday from list of CSV string to list of dates
        holidays = branch_schedule.holidays.split(',')
        holidays = [_localize_date_string(holiday) for holiday in holidays]

        schedule_weekdays = {
            0: (branch_schedule.monday_first_appt, branch_schedule.monday_last_appt),
            1: (branch_schedule.tuesday_first_appt, branch_schedule.tuesday_last_appt),
            2: (branch_schedule.wednesday_first_appt, branch_schedule.wednesday_last_appt),
            3: (branch_schedule.thursday_first_appt, branch_schedule.thursday_last_appt),
            4: (branch_schedule.friday_first_appt, branch_schedule.friday_last_appt),
            5: (branch_schedule.saturday_first_appt, branch_schedule.saturday_last_appt),
        }

        min_start_time_local_tz, max_start_time_local_tz = schedule_weekdays[appointment_weekday]

        if min_start_time_local_tz and max_start_time_local_tz:
            if appointment_start_time < min_start_time_local_tz or appointment_start_time > max_start_time_local_tz:
                error = True

            if appointment_date in holidays:
                error = True
            
        else: # branch has a null value for this date/time
            error = True
        
    else: # no schedule has been created for this branch
        error = True

    if error:
        raise ValidationError('Appointment has been created outside of branch schedule time.')

    return appointment