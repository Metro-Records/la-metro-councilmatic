import re
from datetime import datetime, timedelta

from django.db.models.expressions import RawSQL

from councilmatic_core.models import Event

# Parse the subject line from ocr_full_text
def format_full_text(full_text):
    results = ''

    if full_text:
        full_text_with_cue = full_text.replace('\n\n', 'NEWLINE').replace('\r\n', 'NEWLINE').replace('\n..', 'NEWLINE')

        match = re.search('(SUBJECT:)(.*?)(NEWLINE|ACTION:)', full_text_with_cue.replace('\n', ''))
        if match:
            results = match.group(2)

    return results

def parse_subject(text):
    if ('[PROJECT OR SERVICE NAME]' not in text) and ('[DESCRIPTION]' not in text) and ('[CONTRACT NUMBER]' not in text):
        return text

# Use this helper function when multiple "current meetings" happen simultaneously.
def calculate_current_meetings(found_events, now_with_buffer):
    earliest_start = found_events.first().start_time
    latest_start = found_events.last().start_time
    # Sometimes multiple events happen at the same time (though in reality, they occur one-after-the-other). Example: the committee events at 1:00 on 05/17/2017.
    # Check for this situation, and then determine if these events include a board meeting.
    # If current events do not include a board meeting, the end time should be one hour.
    if earliest_start == latest_start:
        if found_events.filter(name__icontains='Board Meeting'):
            # Custom order: show the board meeting first.
            # '.annotate' adds a field called 'val', which contains a boolean – we order in reverse, since
            # false comes before true.
            return found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
        else:
            one_hour_ago = now_with_buffer - timedelta(hours=1)
            
            return found_events.filter(start_time__gt=one_hour_ago)

    else:
        # To find committee events...
        event_names = [e.name for e in found_events if ("Committee" in e.name) or ("LA SAFE" in e.name) or ("Budget Public Hearing" in e.name) or ("Fare Subsidy Program Public Hearing" in e.name) or ("Crenshaw Project Corporation" in e.name)]

        if event_names:
            # Set meeting time to one hour
            one_hour_ago = now_with_buffer - timedelta(hours=1)
            
            found_events = found_events.filter(start_time__gt=one_hour_ago)

            if len(found_events) > 1:
                return found_events
            else:
                return found_events.first()
        else:
            return found_events.first()                