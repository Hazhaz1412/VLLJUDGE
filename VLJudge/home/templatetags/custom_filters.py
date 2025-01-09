from django import template

register = template.Library()

@register.filter(name='replace_spaces')
def replace_spaces(value):
    return value.replace(' ', '-').lower()

@register.filter
def dict_get(dictionary, key):
    return dictionary.get(key, '')