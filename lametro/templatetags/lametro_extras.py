from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import strip_tags
from django.utils import timezone

from haystack.query import SearchQuerySet
from datetime import date, timedelta, datetime
import re
import urllib

from councilmatic.settings_jurisdiction import *
from councilmatic.settings import PIC_BASE_URL
from councilmatic_core.models import Person, Bill
from councilmatic_core.utils import ExactHighlighter

from lametro.models import LAMetroEvent
from lametro.utils import format_full_text, parse_subject

from opencivicdata.legislative.models import EventDocument

register = template.Library()

@register.filter
def call_link_html(person_id):
    person = Person.objects.get(id=person_id)
    url = person.link_html
    return url

@register.filter
def format_label(label):
    first_part = label.split(', ')[0]

    return first_part

@register.filter
def comma_to_line_break(text):
    return '<br />'.join(text.split(', '))

@register.filter
def format_district(label):
    label_parts = label.split(', ')
    if "Mayor of the City" in label:
        formatted_label = "City of Los Angeles"
    else:
        formatted_label = label_parts[-1]
    return formatted_label

# Filter for legislation detail view
@register.filter
def prepare_title(full_text):
    formatted_text = format_full_text(full_text)

    if formatted_text:
        return parse_subject(formatted_text)


@register.filter
def full_text_doc_url(url):
    query = {'document_url': url, 'filename': 'agenda'}
    pic_query = {'file': PIC_BASE_URL + '?' + urllib.parse.urlencode(query)}

    return urllib.parse.urlencode(pic_query)


'''
This filter converts the post title into a prose-style format with nomination info,
(e.g., "Appointee of Los Angeles County City Selection Committee, Southeast Long Beach sector" into "Appointee of [Committee], nominated by the [Subcommittee]") 
Some posts do not require modification, e.g., "Caltrans District 7 Director, Appointee of Governor of California."
A full list of posts resides in the scraper: https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/people.py
'''
@register.filter
def appointment_label(label):
    # The District 7 Director does not require modification.
    # The scraper imports it as it should be: https://github.com/opencivicdata/scrapers-us-municipal/blob/master/lametro/__init__.py
    if 'District 7 Director' in label:
        return label

    full_label = label.replace("Appointee of", "Appointee of the")
    label_parts = full_label.split(', ')

    if len(label_parts) < 1:
        return full_label
    
    if 'sector' in full_label:
        return ', nominated by the '.join(label_parts).replace('sector', 'Subcommittee')
    else:
        return ', nominated by the '.join(label_parts) + ' Subcommittee'
    

@register.filter
def clean_membership_extras(extras):
    if extras.get('acting'):
        return 'Acting'
    else:
        return ''

@register.filter
def clean_role(role_list):
    if len(role_list) > 1:
        try:
            role_list.remove('Board Member')
        except:
            pass

    return role_list[0]

@register.filter
def compare_time(event_date):
    if event_date < timezone.now():
        return True

@register.filter
def parse_agenda_item(text):
    if text:
        label, number = text.split(',')
        return number
    else: 
        return ''

@register.filter
def short_topic_name(text):
    if len(text) > 40:
        blurb = text[:40]
        blurb = blurb[:blurb.rfind(' ')] + ' ...'
        return blurb
    else:
        return text

@register.filter
def updates_made(event_id):
    ''' 
    When Metro finalizes an agenda, they add it to legistar, and we scrape this link, and add it to our DB. Sometimes, Metro might change the date or time of the event - after adding the agenda. When this occurs, a label indicates that event has been updated.
    This filter determines if an event had been updated after its related EventDocument (i.e., agenda) was last updated. 
    If the below equates as true, then we render a label with the text "Updated", next to the event, on the meetings page. 
    '''

    event = LAMetroEvent.objects.get(ocd_id=event_id)

    try:
        event.documents.get(note__icontains='Agenda')
    except EventDocument.DoesNotExist:
        return False

    return event.updated_at > document.date

@register.filter
def find_agenda_url(all_documents):
    '''
    This filter determines how to format the URL link, particularly, in the case of manually uploaded agenda.
    '''
    valid_urls = [url for x in all_documents if (x.note == 'Agenda' or x.note == 'Event Document - Manual upload URL') for url in x.links.all()]
    pdf_url = [('static/' + url) for x in all_documents if x.note == 'Event Document - Manual upload PDF' for url in x.links.all()]
    valid_urls += pdf_url

    return valid_urls[0]

@register.simple_tag(takes_context=True)
def get_highlighted_attachment_text(context, id):
    bill = Bill.objects.get(id=id)
    attachment_text = ' '.join(d.full_text for d in bill.documents.all() if d.full_text)

    highlight = ExactHighlighter(context['query'])
    
    return highlight.highlight(attachment_text)
