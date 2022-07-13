from django.core.exceptions import ValidationError
from catalog.utils.static_vars import CATEGORIES

def validate(category):
    if category not in CATEGORIES:
        raise ValidationError('Menu category %(category)s is not valid. Valid categories are: %(categories)s.', params={'category': category, 'categories': CATEGORIES})