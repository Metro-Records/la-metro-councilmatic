import re
import pytz
from datetime import datetime, timedelta
import requests
import lxml.html
from lxml.etree import tostring

from django.db.models.expressions import RawSQL
from django.conf import settings

from councilmatic_core.models import EventParticipant, Organization

from lametro.models import LAMetroEvent

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
        return text


def calculate_current_meetings(found_events, now=datetime.now(app_timezone)):
    '''
    Accept a queryset of events that started in the last six hours, or start
    in the next five minutes, and determine which is in progress, by checking
    Legistar for an "In Progress" indicator.

    If there are meetings scheduled concurrently, and one is a board meeting,
    show the board meeting first.

    Based on a spreadsheet of average meeting times from Metro, we assume
    meetings last at least 55 minutes. If any found events started less than
    55 minutes ago, display them as current if the previous meeting has
    ended. Otherwise, check Legistar for the "In Progress" indicator.

    This method should always return a queryset.
    '''
    fifty_five_minutes_ago = now - timedelta(minutes=55)

    # '.annotate' adds a field called 'val', which contains a boolean – we order
    # in reverse, since False comes before True, to show board meetings first.
    found_events = found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',)))\
                               .order_by('-val')

    earliest_start = found_events.earliest('start_time').start_time
    latest_start = found_events.latest('start_time').start_time

    if found_events.filter(start_time__gte=fifty_five_minutes_ago):
        previous_meeting = found_events.filter(start_time__gte=fifty_five_minutes_ago)\
                                       .last()\
                                       .get_previous_by_start_time()

        if legistar_meeting_progress(previous_meeting):
            return LAMetroEvent.objects.filter(ocd_id=previous_meeting.ocd_id)

        return found_events.filter(start_time__gte=fifty_five_minutes_ago)

    elif earliest_start == latest_start:
        # There is one event object, or there are multiple events scheduled to
        # happen at the same time.
        #
        # n.b., In reality, concurrently scheduled events happen one after the
        # other, but we want the current meeting display to line up with the
        # scheduled events (i.e., if it's 9:15, show all of the events slated
        # for 9, even if only one is technically in progress).
        for event in found_events:
            if legistar_meeting_progress(event):
                return found_events

    else:
        for event in found_events:
            if legistar_meeting_progress(event):
                return LAMetroEvent.objects.filter(ocd_id=event.ocd_id)

    return LAMetroEvent.objects.none()


def legistar_meeting_progress(event):
    '''
    This function helps determine the status of a meeting (i.e., is it 'In progess'?).

    Granicus provides a list of current events (video ID only) on http://metro.granicus.com/running_events.php.
    We get that ID and then check if the ID matches that of the event in question.
    '''
    organization_name = EventParticipant.objects.get(event_id=event.ocd_id).entity_name.strip()
    # The strip handles cases where Metro admin added a trailing whitespace to the participant name, e.g., https://ocd.datamade.us/ocd-event/d78836eb-485f-4f5f-b0ce-f89ceaa66d6f/ 
    try: 
        organization_detail_url = Organization.objects.get(name=organization_name).source_url
    except Organization.DoesNotExist: 
        return False

    # Get video ID from Grancius, if one exists.
    running_events = requests.get("http://metro.granicus.com/running_events.php")
    if running_events.json():
        event_id = running_events.json()[0]
    else:
        return False

    organization_detail = requests.get(organization_detail_url)
    if event_id in organization_detail.text:
        return True

    return False
