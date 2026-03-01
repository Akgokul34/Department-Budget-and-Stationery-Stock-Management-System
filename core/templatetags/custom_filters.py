from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Replaces all occurrences of the first character in arg 
    with the second character in arg (if provided as 'old,new') 
    or simply replaces the first string with the second.
    """
    if "," in arg:
        old, new = arg.split(',')
        return value.replace(old, new)
    return value.replace("_", " ")

@register.filter
def percentage(value, total):
    """
    Calculates the percentage of value relative to total.
    """
    try:
        return round((float(value) / float(total)) * 100, 1) if total else 0
    except (ValueError, ZeroDivisionError, TypeError):
        return 0
