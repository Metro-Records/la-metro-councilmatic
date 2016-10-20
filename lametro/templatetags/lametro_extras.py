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
def call_link_html(person_id):
    person = Person.objects.get(ocd_id=person_id)
    link = person.link_html
    return link

@register.filter
def make_formatted_label(label):
    label_parts = label.split(', ')
    formatted_label = '</br>'.join(label_parts)
    return formatted_label
