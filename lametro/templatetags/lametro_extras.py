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
def format_district(label):
    label_parts = label.split(', ')
    if "Mayor of the City" in label:
        formatted_label = "City of Los Angeles"
    else:
        formatted_label = label_parts[-1]
    return formatted_label

@register.filter
def format_full_text(full_text):
    txt_as_array = full_text.split("..")
    results = ""

    for arr in txt_as_array:
        sliced_arr = arr.split( )[1:]
        results += " ".join(sliced_arr) + "<br /><br />"

    return results

@register.filter
def full_text_doc_url(url):
    base_url = 'https://pic.datamade.us/lametro/document/'
    # base_url = 'http://127.0.0.1:5000/lametro/document/'
    doc_url = '{0}?filename=agenda&document_url={1}'.format(base_url,
                                                             url)

    return doc_url

@register.filter
def appointment_label(label):
    full_label = label.replace("Appointee of", "Appointee of the")
    label_parts = full_label.split(', ')
    if len(label_parts) > 1:
        if 'sector' in full_label:
            appointment_label = ', nominated by the '.join(label_parts).replace('sector', 'Subcommittee')
        else:
            appointment_label = ', nominated by the '.join(label_parts) + ' Subcommittee'
    else:
        print(label)
        appointment_label = full_label

    return appointment_label

@register.filter
def parse_subject(text):
    text_slice = text[:200]
    return re.search(r'SUBJECT:(.*?)ACTION:', str(text)).group(1)
