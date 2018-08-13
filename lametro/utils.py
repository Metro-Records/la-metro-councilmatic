import re
import pytz
from datetime import datetime, timedelta
import requests
import lxml.html
from lxml.etree import tostring

from django.conf import settings

from councilmatic_core.models import EventParticipant, Organization, Event, Action

app_timezone = pytz.timezone(settings.TIME_ZONE)

def format_full_text(full_text):
    '''
    The search results and board report titles (on the BillDetail) should show the "SUBJECT:" header from the board report when present.
    The ocr_full_text contains this information. Some example snippets:

    # Subject header followed by two linebreaks.
    ..Subject\nSUBJECT:\tFOOD SERVICE OPERATOR\n\n..Action\nACTION:\tAWARD SERVICES CONTRACT\n\n..

    # Subject header followed by a return carriage and linebreak.
    ..Subject/Action\r\nSUBJECT: MONTHLY REPORT ON CRENSHAW/LAX SAFETY\r\nACTION: RECEIVE AND FILE\r\n

    # Subject header with a linebreak in the middle and without an ACTION header.
    ..Subject\nSUBJECT:    REVISED MOTION BY DIRECTORS HAHN, SOLIS, \nGARCIA, AND DUPONT-WALKER\n..Title\n
    '''
    results = ''

    if full_text:
        clean_full_text = full_text.replace('\n\n', 'NEWLINE').replace('\r\n', 'NEWLINE').replace('\n..', 'NEWLINE').replace('\n', ' ')
        match = re.search('(SUBJECT:)(.*?)(NEWLINE|ACTION:)', clean_full_text)
        if match:
            results = match.group(2)

    return results

def parse_subject(text):
    if ('[PROJECT OR SERVICE NAME]' not in text) and ('[DESCRIPTION]' not in text) and ('[CONTRACT NUMBER]' not in text):
        return text.strip()

def find_last_action_date(bill_ocd_id):
    '''
    Several Metro bills do not have "histories." 
    Discussed in this issue: 
    https://github.com/datamade/la-metro-councilmatic/issues/340

    If a bill does not have a history, then determine its `last_action_date` by looking for the most recent agenda that references the bill. 
    '''
    actions = Action.objects.filter(_bill_id=bill_ocd_id)
    last_action_date = ''

    if actions:
        last_action_date = actions.reverse()[0].date
    else:
        events = Event.objects.filter(agenda_items__bill_id=bill_ocd_id)
        if events:
            last_action_date = events.latest('start_time').start_time

    return last_action_date