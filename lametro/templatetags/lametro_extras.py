from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import strip_entities, strip_tags
from django.utils import timezone

from haystack.query import SearchQuerySet
from datetime import date, timedelta, datetime
import re

from councilmatic.settings_jurisdiction import *
from councilmatic_core.models import Person, Event

register = template.Library()

@register.filter
def call_headshot_url(person_id):
    person = Person.objects.get(ocd_id=person_id)
    url = person.headshot_url
    return url

@register.filter
def call_link_html(person_id):
    person = Person.objects.get(ocd_id=person_id)
    url = person.link_html
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
    results = ''

    if full_text:
        txt_as_array = full_text.split("..")

        for arr in txt_as_array:
            if arr:
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
    text_snippet = ''

    if text:
        text_slice = text[:300]
        re_results = re.search(r'SUBJECT:(.*?)ACTION:', str(text))
        if re_results:
            text_snippet = re_results.group(1)

    return text_snippet

@register.filter
def clean_role(role_list):
    if len(role_list) > 1:
        try:
            role_list.remove('Board Member')
        except:
            pass

    return role_list[0]

@register.filter
def clean_label(label_list):
    label_list = [ label for label in label_list if 'Chair' not in label ]
    label = label_list[0]

    return label

@register.filter
def format_string(label_list):
    label_list = label_list.replace('{', '').replace('}', '').replace('"', '')

    return label_list.split(',')

@register.filter
def get_minutes(event_id):
    event = Event.objects.get(ocd_id=event_id)

    doc = event.documents.filter(note__icontains='RBM Minutes').first()

    if doc:
        return doc.url
    else:
        date = event.start_time.date().strftime('%B %d, %Y')
        content = 'minutes of the regular board meeting held ' + date
        sqs = SearchQuerySet().filter(content=content).all()
        if sqs:
            for q in sqs:
                if q.object.bill_type == 'Minutes' and q.object.slug:

                    if re.search(content, q.object.ocr_full_text, re.IGNORECASE):
                        return '/board-report/' + q.object.slug
        else:
            return None

@register.filter
def compare_time(event_date):
    if event_date < timezone.now():
        return True

@register.filter
@stringfilter
def short_title(text_blob):
    session_dict = {
        '2014': '7/1/2014 to 6/30/2015',
        '2015': '7/1/2015 to 6/30/2016',
        '2016': '7/1/2016 to 6/30/2017',
    }
    if text_blob in ['2014', '2015', '2016', '2017']:
        return session_dict[text_blob]
    elif len(text_blob) > 28:
        blurb = text_blob[:24]
        blurb = blurb[:blurb.rfind(' ')] + ' ...'
        return blurb
    else:
        return text_blob

@register.filter
def parse_agenda_item(text):
    if text:
        label, number = text.split(',')
        return number