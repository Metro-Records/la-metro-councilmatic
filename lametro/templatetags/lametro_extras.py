from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import strip_entities, strip_tags
from councilmatic.settings_jurisdiction import *
from councilmatic_core.models import Person
import re

register = template.Library()

@register.filter
def call_headshot_url(person_id):
    person = Person.objects.get(ocd_id=person_id)
    url = person.headshot_url
    return url

@register.filter
def format_label(label):
    label_parts = label.split(', ')
    formatted_label = '<br />'.join(label_parts)
    return formatted_label

@register.filter
def format_full_text(full_text):
    txt_as_array = full_text.split("..")
    results = ""

    for arr in txt_as_array:
        sliced_arr = arr.split( )[1:]
        results += " ".join(sliced_arr) + "<br /><br />"

    return results