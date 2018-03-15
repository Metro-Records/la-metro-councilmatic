import pytz
from datetime import datetime, timedelta
import requests
import lxml.html
from lxml.etree import tostring

from django.db.models.expressions import RawSQL
from django.conf import settings

from councilmatic_core.models import Event, EventParticipant, Organization

app_timezone = pytz.timezone(settings.TIME_ZONE)

# Parse the subject line from ocr_full_text
def format_full_text(full_text):
    results = ''

    if full_text:
        txt_as_array = full_text.split("..")
        for item in txt_as_array:
            if 'SUBJECT:' in item:
                array_with_subject = item.split('\n\n')
                for item in array_with_subject:
                    if 'SUBJECT:' in item:
                        results = item.replace('\n', '')
    return results

# Isolate text after 'SUBJECT'
def parse_subject(text):
    if text:
        before_keyword, keyword, after_keyword = text.partition('SUBJECT:')
        if after_keyword:
            if '[PROJECT OR SERVICE NAME]' not in after_keyword and '[DESCRIPTION]' not in after_keyword and '[CONTRACT NUMBER]' not in after_keyword:
                return after_keyword.strip()

    return None


def calculate_current_meetings(found_events, five_minutes_from_now):
    # Metro provided a spreadsheet of average meeting times. The minimum average time a meeting lasts is 52 minutes: let's round down to 50 and add the 5-minute buffer, i.e., an event will appear, regardless of Legistar, for 55 minutes past its start time. 
    # time_ago = five_minutes_from_now - timedelta(minutes=60)
    time_ago = five_minutes_from_now - timedelta(minutes=50)

    # Custom order: show the board meeting first, when there is one.
    # '.annotate' adds a field called 'val', which contains a boolean – we order in reverse, since false comes before true.
    found_events = found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
    earliest_start = found_events.earliest('start_time').start_time 
    latest_start = found_events.latest('start_time').start_time 

    if found_events.filter(start_time__gte=time_ago):
        # Check if previous event is still going on in Legistar.
        previous_meeting = found_events.filter(start_time__gte=time_ago).last().get_previous_by_start_time()
        if legistar_meeting_progress(previous_meeting):
            return Event.objects.filter(ocd_id=previous_meeting.ocd_id)

        return found_events.filter(start_time__gte=time_ago)  
    elif earliest_start == latest_start:  
        # The IF statement handles the below cases:
        # (1) found_events includes just one event object. Example: the first committee meeting of the day - 9:00 am on 01/18/2018
        # (2) found_events includes multiple events that all happen at the same time (though in reality, they occur one-after-the-other). Example: the events at 9:00 am on 11/30/2017
        for event in found_events:
            if legistar_meeting_progress(event):
                return found_events
    else: 
        for event in found_events:
            if legistar_meeting_progress(event):
                # The template expects a queryset
                return Event.objects.filter(ocd_id=event.ocd_id)

    return Event.objects.none()


def legistar_meeting_progress(event):
    '''
    This function helps determine the status of a meeting (i.e., is it 'In progess'?).

    Granicus provides a list of current events (video ID only) on http://metro.granicus.com/running_events.php.
    We get that ID and then check if the ID matches that of the event in question.
    '''
    organization_name = EventParticipant.objects.get(event_id=event.ocd_id).entity_name

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
