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

# Use this helper function when multiple "current meetings" happen simultaneously.
def calculate_current_meetings(found_events, now_with_buffer):
    earliest_start = found_events.first().start_time
    latest_start = found_events.last().start_time
    # The IF statement handles the below cases:
    # (1) found_events includes just one event object. Example: the first committee meeting of the day - 9:00 am on 01/18/2018
    # (2) found_events includes multiple events that all happen at the same time (though in reality, they occur one-after-the-other). Example: the events at 9:00 am on 11/30/2017
    # Check for these situations, and then determine if the found_events include a board meeting.
    # If so, then the start_time should remain greater than "three hours ago."
    # If not, then the start_time should be determined by that of the next meeting. 
    if earliest_start == latest_start:
        # OLD CODE
        if found_events.filter(name__icontains='Board Meeting'):
            # Custom order: show the board meeting first.
            # '.annotate' adds a field called 'val', which contains a boolean – we order in reverse, since
            # false comes before true.
            return found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
        else:
            event = found_events.first()
            time_ago = now_with_buffer - calculate_meeting_duration(event)

            return found_events.filter(start_time__gt=time_ago)


        # found_events = found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
        # Minimum average time a meeting lasts. 
        # time_ago = now_with_buffer - timedelta(minutes=48)
        # if ordered_found_events.filter(start_time__gt=time_ago):
        #     # Check if previous event is still going on in Legistar.
        #     previous_meeting = ordered_found_events.first().get_previous_by_start_time()

        #     if legistar_meeting_progress(previous_meeting):
        #         return [previous_meeting]
    
        #     return ordered_found_events
           
        # else:  
        #     # Check if this event is still going on.
        #     if legistar_meeting_progress(ordered_found_events.first()):
        #         return ordered_found_events

        #     return []


    # Most often, the found_events includes several event objects with different start times. 
    # Why? The found_events object includes all events from three hours ago.
    # Determine if found_events has committee events.
    else:
        # OLD
        event_names = [e.name for e in found_events if ("Committee" in e.name) or ("LA SAFE" in e.name) or ("Budget Public Hearing" in e.name) or ("Fare Subsidy Program Public Hearing" in e.name) or ("Crenshaw Project Corporation" in e.name) or ("TAP Public Hearing" in e.name)]

        if event_names:
            # Find the latest event, since found_events may contain an earlier committee event that has ended.
            event = found_events.last()
            time_ago = now_with_buffer - calculate_meeting_duration(event)
            last_event = event.get_previous_by_start_time()

            return found_events.filter(start_time__gt=time_ago).filter(start_time__gt=last_event.start_time)
        else:
            return found_events  



        
    # # Minimum average time a meeting lasts. 
    # time_ago = now_with_buffer - timedelta(minutes=60)

    # if found_events.filter(start_time__gt=time_ago):
    #     # Check if previous event is still going on in Legistar.
    #     previous_meeting = found_events.last().get_previous_by_start_time()

    #     if legistar_meeting_progress(previous_meeting):
    #         return Event.objects.filter(ocd_id=previous_meeting.ocd_id)

    #     return found_events.filter(start_time__gt=time_ago)
       
    # else:  
    #     # Check if this event is still going on.
    #     if legistar_meeting_progress(found_events.last()):
    #         return found_events

    #     return Event.objects.none()




def calculate_meeting_duration(event):
    next_event = event.get_next_by_start_time()
    # Are two committee meetings happening concurrently?
    if next_event.start_time == event.start_time:
        next_event = next_event.get_next_by_start_time()

    meeting_duration = next_event.start_time - event.start_time
    # meeting_duration can be one hour or greater, e.g., 1 hour and 9 minutes.
    # However, meeting_duration cannot be greater than 120 minutes. 
    if meeting_duration > timedelta(minutes=60):
        meeting_duration = timedelta(minutes=60)

    return meeting_duration

# def compare_to_previous_meeting(event):
#     calculated_current_meeting = event.first()
#     previous_meeting = calculated_current_meeting.get_previous_by_start_time()

#     # Hit legistar
#     organization_name = EventParticipant.objects.get(event_id=previous_meeting.ocd_id).entity_name
#     organization_detail_url = Organization.objects.get(name=organization_name).source_url

#     import requests

#     r = requests.get(organization_detail_url)
#     if 'In&amp;nbsp;progress' in r.content.decode('utf-8'):
#         return previous_meeting
#     else:
#         return event

def legistar_meeting_progress(event):
    organization_name = EventParticipant.objects.get(event_id=event.ocd_id).entity_name
    organization_detail_url = Organization.objects.get(name=organization_name).source_url

    r = requests.get(organization_detail_url)
    event_date = '{month}/{day}/{year}'.format(month=event.start_time.month, day=event.start_time.day, year=event.start_time.year)

    return 'In&amp;nbsp;progress' in r.content.decode('utf-8') and event_date in r.content.decode('utf-8')
