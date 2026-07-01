from django import template

register = template.Library()

@register.filter
def starts_with(value, prefix):
    return value.startswith(prefix)