from django.core.exceptions import ValidationError
from catalog.models import NewAppt
from catalog.utils.static_vars import MAX_SERVICES_PER_APPOINTMENT

def validate(appointment):
    customer = appointment['customer']
    appointments = NewAppt.objects.filter(customer=customer)
    
    if len(appointments) >= MAX_SERVICES_PER_APPOINTMENT:
        raise ValidationError('Maximum appointments reached [%(max)s].', params={'max': MAX_SERVICES_PER_APPOINTMENT})
    return appointment