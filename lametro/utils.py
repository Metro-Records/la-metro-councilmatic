from datetime import datetime, timedelta
import requests

from django.db.models.expressions import RawSQL

from councilmatic_core.models import Event, EventParticipant, Organization

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


def calculate_current_meetings(found_events, now_with_buffer):
    # Metro provided a spreadsheet of average meeting times. The minimum average time a meeting lasts is 52 minutes: let's round to 55 and remove the 5-minute buffer. 
    time_ago = now_with_buffer - timedelta(minutes=60)
    # Custom order: show the board meeting first, when there is one.
    # '.annotate' adds a field called 'val', which contains a boolean – we order in reverse, since false comes before true.
    found_events = found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')

    if found_events.filter(start_time__gte=time_ago):
        # Check if previous event is still going on in Legistar.
        previous_meeting = found_events.filter(start_time__gte=time_ago).last().get_previous_by_start_time()
        if legistar_meeting_progress(previous_meeting):
            return Event.objects.filter(ocd_id=previous_meeting.ocd_id)

        return found_events.filter(start_time__gte=time_ago)  
    else:  
        # The IF statement handles the below cases:
        # (1) found_events includes just one event object. Example: the first committee meeting of the day - 9:00 am on 01/18/2018
        # (2) found_events includes multiple events that all happen at the same time (though in reality, they occur one-after-the-other). Example: the events at 9:00 am on 11/30/2017
        earliest_start = found_events.first().start_time
        latest_start = found_events.last().start_time 

        if earliest_start == latest_start:
            for event in found_events:
                if legistar_meeting_progress(event):
                    return found_events
        else: 
            if legistar_meeting_progress(found_events.last()):
                return Event.objects.filter(ocd_id=found_events.last().ocd_id)

        return Event.objects.none()


def legistar_meeting_progress(event):
    in_progress = False
    organization_name = EventParticipant.objects.get(event_id=event.ocd_id).entity_name

    try: 
        organization_detail_url = Organization.objects.get(name=organization_name).source_url
    except Organization.DoesNotExist: 
        return in_progress

    r = requests.get(organization_detail_url)
    event_date = '{month}/{day}/{year}'.format(month=event.start_time.month, day=event.start_time.day, year=event.start_time.year)
    in_progress = 'In&amp;nbsp;progress' in r.content.decode('utf-8') and event_date in r.content.decode('utf-8')
    
    return in_progress
