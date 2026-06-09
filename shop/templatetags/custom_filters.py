from django import template

register = template.Library()

@register.filter(name='abs_value')
def abs_value(value):
    try:
        return abs(float(value)) if value is not None else 0
    except (ValueError, TypeError):
        return 0
