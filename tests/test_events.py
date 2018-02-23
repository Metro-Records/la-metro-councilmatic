import pytest
from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from councilmatic_core.models import Event, EventDocument, Bill, RelatedBill

from lametro.models import LAMetroEvent
from lametro.templatetags.lametro_extras import updates_made
from lametro.forms import AgendaPdfForm
from lametro.utils import calculate_current_meetings

# This collection of tests checks the functionality of Event-specific views, helper functions, and relations.
def test_agenda_creation(event, event_document):
    '''
    Test that the same agenda url does not get added twice.
    '''
    event = event.build()
    agenda = event_document.build()

    agenda, created = EventDocument.objects.get_or_create(event=event, url='https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081')
    assert not created == True


def test_agenda_pdf_form_submit():
    '''
    This unit test checks that a pdf validates the form.
    '''

    with open('tests/test_agenda.pdf', 'rb') as agenda:
        agenda_file = agenda.read()

        agenda_pdf_form = AgendaPdfForm(files={'agenda': SimpleUploadedFile('test_agenda.pdf', agenda_file, content_type='application/pdf')})
    
        assert agenda_pdf_form.is_valid() == True


def test_agenda_pdf_form_error():
    '''
    This unit test checks that a non-pdf raises an error.
    '''

    with open('tests/test_image.gif', 'rb') as agenda:
        bad_agenda_file = agenda.read()

        agenda_pdf_form = AgendaPdfForm(files={'agenda': SimpleUploadedFile('test_image.gif', bad_agenda_file, content_type='image/gif')})

        assert agenda_pdf_form.is_valid() == False


def test_updates_made_true(event, event_document):
    '''
    This test examines the relation between an event and its EventDocument.
    The test updates the Event. Thus, the Event reads as updated after the Agenda: the template tag should return True.
    '''
    event = event.build()
    agenda = event_document.build()

    # Make an update!
    event.updated_at = datetime.now()
    event.save()

    assert updates_made(event.ocd_id) == True


def test_updates_made_false(event, event_document):
    '''
    This test examines the relation between an event and its EventDocument. 
    The test updates the Agenda. Thus, the Event is not updated after the Agenda: the template tag should return False.
    '''
    event = event.build()
    agenda = event_document.build()

    # Make an update!
    agenda.updated_at = datetime.now()
    agenda.save()

    assert updates_made(event.ocd_id) == False    

# @pytest.mark.django_db
# def test_current_committee_meeting_first(django_db_setup):
#     '''
#     This test insures that the `calculate_current_meetings` function returns the first committee event, in a succession of events.
#     For this case, the meeting is at 11:00 am, and a 12:15 pm meeting follows.
#     '''
#     # Set the time to 10:55 pm (i.e., five minutes before an 11:00 event).
#     six_minutes_from_now = datetime(2017,5,18,10,55) + timedelta(minutes=6)
#     three_hours_ago = datetime(2017,5,18,10,55) - timedelta(hours=3)
#     found_events = Event.objects.filter(start_time__lt=six_minutes_from_now)\
#               .filter(start_time__gt=three_hours_ago)\
#               .exclude(status='cancelled')\
#               .order_by('start_time')

#     assert len(found_events) == 1

#     current_meeting = calculate_current_meetings(found_events, six_minutes_from_now)

#     assert len(current_meeting) == 1
#     assert current_meeting.first().name == 'Construction Committee'

# @pytest.mark.django_db
# def test_current_committee_meeting_last(django_db_setup):
#     '''
#     This test insures that the `calculate_current_meetings` function returns the second and last committee event, in a succession of events.
#     For this case, the meeting is at 12:15 pm, and no other events follow.
#     '''
#     # Set the time to 12:10 pm (i.e., five minutes before a 12:15 event).
#     six_minutes_from_now = datetime(2017,5,18,12,10) + timedelta(minutes=6)
#     three_hours_ago = datetime(2017,5,18,12,10) - timedelta(hours=3)
#     found_events = Event.objects.filter(start_time__lt=six_minutes_from_now)\
#               .filter(start_time__gt=three_hours_ago)\
#               .exclude(status='cancelled')\
#               .order_by('start_time')

#     assert len(found_events) > 1

#     current_meeting = calculate_current_meetings(found_events, six_minutes_from_now)

#     assert len(current_meeting) == 1
#     assert current_meeting.first().name == 'System Safety, Security and Operations Committee'