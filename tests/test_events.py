import pytest
import pytz
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


@pytest.mark.parametrize('now,progress_value,num_found,num_current,name', [
    (datetime(2018,1,18,8,55), False, 1, 1, 'System Safety, Security and Operations Committee'),
    (datetime(2018,1,18,9,54), False, 1, 1, 'System Safety, Security and Operations Committee'),
    (datetime(2018,1,18,10,1), True, 1, 1, 'System Safety, Security and Operations Committee'),
    (datetime(2018,1,18,10,1), False, 1, 0, 'System Safety, Security and Operations Committee'),
    (datetime(2018,1,18,10,10), False, 2, 1, 'Construction Committee'),
    (datetime(2018,1,18,10,10), True, 2, 1, 'System Safety, Security and Operations Committee'),
    (datetime(2018,1,18,11,9), False, 2, 1, 'Construction Committee'),
    (datetime(2017,11,30,8,55), False, 2, 2, 'Regular Board Meeting'),
    (datetime(2017,11,30,9,54), False, 2, 2, 'Regular Board Meeting'),
])
def test_current_committee_meeting_first(event, 
                                         mocker, 
                                         now,
                                         progress_value,
                                         num_found,
                                         num_current,
                                         name):
    '''
    This test insures that the `calculate_current_meetings` function returns the first committee event, in a succession of events.
    This test considers four cases to determine if the 'System Safety, Security and Operations Committee' should appear as current:
    (1) Set the time to 8:55 am (i.e., five minutes before a 9:00 event, when the event should first appear).
    (2) Set the time to 9:54 am: the event should continue, regardless of Legistar.
    (3) Set the time to 10:01 am: the event should continue, because Legistar lists it as "In progress."
    (4) Set the time to 10:01 am: the event should NOT continue, because Legistar does not list it as "In progress."
    
    This test considers five cases to determine if the 'Construction Committee' meeting should appear as current:
    (1) Set the time to 10:10 am (i.e., five minutes before a 10:15 event, when the event should first appear). Assume that the previous event ('System Safety') has ended.
    (2) Set the time to 10:10 am (i.e., five minutes before a 10:15 event, when the event should first appear) - however, assume that the previous event ('System Safety') has NOT ended.
    (3) Set the time to 11:09 am: the meeting should continue, regardless of Legistar.
    (4) Set the time to 11:10 am: the meeting should continue, because Legistar lists it as "In progress."
    (5) Set the time to 11:10 am: the meeting should NOT continue, because Legistar does not list it as "In progress."

    This consider cases to determine if a Board Meeting and Crenshaw Project meeting should appear as concurrent, with the Board Meeting first in the queryset:
    (1) Set the time to 8:55 am (i.e., five minutes before a 9:00 event, when the event should first appear).
    (2) Set the time to 9:54 am: the events should continue regardless of Legistar.
    '''

    planning_meeting_info = {
        'ocd_id': 'ocd-event/4cb9995c-c42f-4eb9-a8b4-f8e135045661',
        'name': 'Planning and Programming Committee', 
        'start_time': '2018-01-17 2:00:00',
        'slug': 'planning-and-programming-committee-f8e135045661'
    }
    event.build(**planning_meeting_info)

    safety_meeting_info = {
        'ocd_id': 'ocd-event/5e84e91d-279c-4c83-a463-4a0e05784b62',
        'name': 'System Safety, Security and Operations Committee', 
        'start_time': '2018-01-18 9:00:00',
    }
    event.build(**safety_meeting_info)

    construction_meeting_info = {
        'ocd_id': 'ocd-event/0e793ec8-5091-4099-a115-0560d127d6f9',
        'name': 'Construction Committee', 
        'start_time': '2018-01-18 10:15:00',
        'slug': 'construction-committee-0560d127d6f9'
    }
    event.build(**construction_meeting_info)
    
    ad_hoc_meeting_info = {
        'ocd_id': 'ocd-event/b9b16626-55ef-41fd-bbdb-bf5f259d416b',
        'name': 'Ad-Hoc Customer Experience Committee', 
        'start_time': '2017-11-16 1:00:00',
        'slug': 'ad-hoc-customer-experience-committee-bf5f259d416b'
    }
    event.build(**ad_hoc_meeting_info)

    board_meeting_info = {
        'ocd_id': 'ocd-event/ef33b22d-b166-458f-b254-b81f656ffc09',
        'name': 'Regular Board Meeting', 
        'start_time': '2017-11-30 9:00:00',
        'slug': 'regular-board-meeting-b81f656ffc09'
    }
    event.build(**board_meeting_info)

    crenshaw_meeting_info = {
        'ocd_id': 'ocd-event/3c93e81f-f1a9-42ce-97fe-30c77a4a6740',
        'name': 'Crenshaw Project Corporation', 
        'start_time': '2017-11-30 9:00:00',
        'slug': 'crenshaw-project-corporation-30c77a4a6740'
    }
    event.build(**crenshaw_meeting_info)

    five_minutes_from_now = now + timedelta(minutes=5)
    six_hours_ago = now - timedelta(hours=6)
    found_events = Event.objects.filter(start_time__lte=five_minutes_from_now)\
              .filter(start_time__gte=six_hours_ago)\
              .exclude(status='cancelled')\
              .order_by('start_time')

    assert len(found_events) == num_found

    # Mock this helper function to return true or false, when checking for progress of the previous meeting (which otherwise requires hitting Legistar).
    mocker.patch('lametro.utils.legistar_meeting_progress',
                 return_value=progress_value)

    current_meeting = calculate_current_meetings(found_events, five_minutes_from_now)

    assert len(current_meeting) == num_current
    if current_meeting.first():
        assert current_meeting.first().name == name
