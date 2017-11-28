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
def calculate_current_meetings(found_events, meeting_time):
    start_check = found_events.first().start_time
    end_check = found_events.last().start_time
    # Sometimes multiple events happen at the same time (though in reality, they occur one-after-the-other). Example: the committee events at 1:00 on 05/17/2017.
    # Check for this situation, and then determine if these events include a board meeting.
    # If current events do not include a board meeting, the end time should be one hour.
    if start_check == end_check:
        if found_events.filter(name__icontains='Board Meeting'):
            # Custom order: show the board meeting first.
            print(found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val').query)
            return found_events.annotate(val=RawSQL("name like %s", ('%Board Meeting%',))).order_by('-val')
        else:
            meeting_end_time = meeting_time - timedelta(hours=1)
            
            return Event.objects.filter(start_time__lt=meeting_time)\
                      .filter(start_time__gt=meeting_end_time)\
                      .exclude(status='cancelled')\
                      .order_by('start_time')
    else:
        # To find committee events...
        event_names = [e.name for e in found_events if ("Committee" in e.name) or ("LA SAFE" in e.name) or ("Budget Public Hearing" in e.name) or ("Fare Subsidy Program Public Hearing" in e.name) or ("Crenshaw Project Corporation" in e.name)]

        if len(event_names) > 0:
            # Set meeting time to one hour
            meeting_end_time = meeting_time - timedelta(hours=1)
            
            found_events = Event.objects.filter(start_time__lt=meeting_time)\
                      .filter(start_time__gt=meeting_end_time)\
                      .exclude(status='cancelled')\
                      .order_by('start_time')

            if len(found_events) > 1:
                return found_events
            else:
                return found_events.first()
        else:
            return found_events.first()                