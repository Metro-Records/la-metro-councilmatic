from datetime import datetime, timedelta

from django.db.models.expressions import RawSQL

from councilmatic_core.models import Event

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
    
    # This DO NOT work: if it's 1:00 on 1/17, then the found_events list will still include the 11:00 am meeting on 1/17.....so the logic will always default to the ELSE (which assumes just one meeting)


    # Sometimes, the found_events include just one event object. Example: the first committee meeting of the day - 9:00 am on 01/18/2018
    # Sometimes, multiple events happen at the same time (though in reality, they occur one-after-the-other). Example: the committee events at 1:00 pm on 05/17/2017.
    # Check for these situations, and then determine if the found_events include a board meeting.
    # If so, then the start_time should remain greater than "three hours ago."
    # If not, then the start_time should be determined by that of the next meeting. 
    if earliest_start == latest_start:
        if found_events.filter(name__icontains='Board Meeting'):
            # Custom order: show the board meeting first.
            # '.annotate' adds a field called 'val', which contains a boolean – we order in reverse, since
            # false comes before true.
            return found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
        else:
            event = found_events.first()

            next_event_start_time = event.get_next_by_start_time().start_time
            meeting_duration = next_event_start_time - event.start_time
            # This can be one hour or greater, e.g., 1 hour and 9 minutes
            time_ago = now_with_buffer - meeting_duration

            return found_events.filter(start_time__gt=time_ago)

    # Most often, the found_events includes several event objects with different start times. 
    # Why? The found_events object includes all events from three hours ago.
    # Determine if found_events has committee events.
    else:
        print("here!!!")
        # To find committee events...
        event_names = [e.name for e in found_events if ("Committee" in e.name) or ("LA SAFE" in e.name) or ("Budget Public Hearing" in e.name) or ("Fare Subsidy Program Public Hearing" in e.name) or ("Crenshaw Project Corporation" in e.name)]

        if event_names:
            event = found_events.last()

            next_event_start_time = event.get_next_by_start_time().start_time
            meeting_duration = next_event_start_time - event.start_time
            # meeting_duration can be one hour or greater, e.g., 1 hour and 9 minutes.
            # However, meeting_duration cannot be greater than 90 minutes. 
            if meeting_duration > timedelta(minutes=120):
                meeting_duration = timedelta(minutes=120)

            time_ago = now_with_buffer - meeting_duration

            return found_events.filter(start_time__gt=time_ago)
        else:
            return found_events              