import pytest
import re
from datetime import datetime, timedelta
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.db.models.query import QuerySet
from django.utils import timezone
from django.urls import reverse
from freezegun import freeze_time
import requests
import requests_mock
from unittest.mock import patch

from opencivicdata.legislative.models import EventDocument, EventLocation
from councilmatic_core.models import Bill

from lametro.models import LAMetroEvent, app_timezone
from lametro.views import LAMetroEventDetail
from lametro.templatetags.lametro_extras import updates_made
from lametro.forms import AgendaPdfForm


def mock_streaming_meetings(mocker, return_value=None):
    mock_response = mocker.MagicMock(spec=requests.Response)
    mock_response.json.return_value = return_value if return_value else []
    mock_response.status_code = 200

    mocker.patch('lametro.models.requests.get', return_value=mock_response)

    return mock_response


def test_agenda_creation(event, event_document):
    '''
    Test that the same agenda url does not get added twice.
    '''
    event = event.build()
    agenda = event_document.build()

    agenda, created = EventDocument.objects.get_or_create(event=event)

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


@pytest.mark.parametrize('has_updates,has_agenda', [
    (True, True),
    (True, False),
    (False, True),
    (False, False),
])
def test_updates_made(event, event_document, mocker, has_updates, has_agenda):
    if has_updates:
        updated_at = LAMetroEvent._time_ago(days=1)
    else:
        updated_at = LAMetroEvent._time_ago(days=7)

    # `updated_at` is an auto_now field, which means that it's always updated to
    # the current date on save. Mock that attribute to return values useful for
    # testing. More on auto_now:
    # https://docs.djangoproject.com/en/3.0/ref/models/fields/#django.db.models.DateField.auto_now
    mock_update = mocker.patch('lametro.models.LAMetroEvent.updated_at', new_callable=mocker.PropertyMock)
    mock_update.return_value = updated_at

    event = event.build(start_date=datetime.now().isoformat()[:25])

    if has_agenda:
        document = event_document.build(note='Agenda')
    else:
        document = event_document.build(note='Some document')

    event.documents.add(document)

    assert updates_made(event.id) == (has_updates and has_agenda)

    if not has_updates:
        # Also test updates after start time
        updated_at = LAMetroEvent._time_from_now(days=3)
        mock_update.return_value = updated_at
        assert updates_made(event.id) == (has_updates and has_agenda)


def test_current_meeting_streaming_event(concurrent_current_meetings, mocker):
    '''
    Test that if an event is streaming, it alone is returned as current.
    '''
    dummy_guid = 'a super special guid'

    # Add dummy GUID to one of our events.
    live_meeting, _ = concurrent_current_meetings
    live_meeting.extras = {'guid': dummy_guid.upper()}  # GUIDs in the Legistar API are all caps.
    live_meeting.save()

    mock_streaming_meetings(mocker, return_value=[dummy_guid])

    current_meetings = LAMetroEvent.current_meeting()

    # Assert that we returned the streaming meeting.
    assert current_meetings.get() == live_meeting


def test_current_meeting_no_streaming_event(concurrent_current_meetings,
                                            mocker):
    '''
    Test that if an event is not streaming, and there are concurrently
    scheduled events, both events are returned as current.
    '''
    mock_streaming_meetings(mocker)

    current_meetings = LAMetroEvent.current_meeting()

    # Test that the board meeting is returned first.
    assert current_meetings.first().name == 'Regular Board Meeting'

    # Test that both meetings are returned.
    assert all(m in current_meetings for m in concurrent_current_meetings)


def test_current_meeting_no_streaming_event_late_start(event, mocker):
    '''
    Test that if an meeting is scheduled but not yet streaming, it is returned
    as current up to 20 minutes past its scheduled start.
    '''
    # Build an event scheduled to start 15 minutes ago.
    crenshaw_meeting_info = {
        'id': 'ocd-event/3c93e81f-f1a9-42ce-97fe-30c77a4a6740',
        'name': 'Crenshaw Project Corporation',
        'start_date': LAMetroEvent._time_ago(minutes=15)\
            .replace(second=0, microsecond=0)\
            .isoformat(),
    }
    late_current_meeting = event.build(**crenshaw_meeting_info)

    mock_streaming_meetings(mocker)

    current_meetings = LAMetroEvent.current_meeting()

    # Assert that we returned the late meeting.
    assert current_meetings.get() == late_current_meeting


def test_current_meeting_no_potentially_current(event):
    '''
    Test that if there are no potentially current meetings (scheduled to
    start in the last six hours, or in the next five minutes), no meetings
    are returned as current.
    '''
    # Build an event outside of the "potentially current" timeframe.
    safety_meeting_info = {
        'id': 'ocd-event/5e84e91d-279c-4c83-a463-4a0e05784b62',
        'name': 'System Safety, Security and Operations Committee',
        'start_date': LAMetroEvent._time_from_now(hours=12)\
            .replace(second=0, microsecond=0)\
            .isoformat(),
    }
    event.build(**safety_meeting_info)

    current_meetings = LAMetroEvent.current_meeting()

    # Assert we did not return any current meetings.
    assert not current_meetings


def test_upcoming_meetings_are_not_marked_as_broadcast(concurrent_current_meetings, mocker):
    # Create two potentially current meetings
    test_event_a, test_event_b = concurrent_current_meetings

    mock_streaming_meetings(mocker)

    # Assert the events are returned (potentially current), but not marked as
    # having been broadcast
    current_meetings = LAMetroEvent.current_meeting()
    assert current_meetings.count() == 2

    for e in (test_event_a, test_event_b):
        assert e in current_meetings

        e.refresh_from_db()
        assert not e.extras.get('has_broadcast', False)


def test_streamed_meeting_is_marked_as_broadcast(concurrent_current_meetings, mocker):
    # Create two potentially current meetings
    test_event_a, test_event_b = concurrent_current_meetings

    # Return the event from the running events endpoint
    dummy_guid = 'a super special guid'

    test_event_a.extras = {'guid': dummy_guid.upper()}  # GUIDs in the Legistar API are all caps.
    test_event_a.save()

    mock_response = mock_streaming_meetings(mocker, return_value=[dummy_guid])

    # Assert Event A is the only event returned, and is marked as having
    # been broadcast and has the correct status
    current_meeting = LAMetroEvent.current_meeting()
    assert current_meeting.get() == test_event_a

    test_event_a.refresh_from_db()
    assert test_event_a.extras['has_broadcast']

    assert test_event_a.is_ongoing
    assert not any([test_event_a.is_upcoming, test_event_a.has_passed])

    # Assert Event B has not been marked as broadcast and is still upcoming
    test_event_b.refresh_from_db()
    assert not test_event_b.extras.get('has_broadcast', False)

    assert test_event_b.is_upcoming
    assert not any([test_event_b.is_ongoing, test_event_b.has_passed])

    # Fast forward an hour, no longer return Event A from the running events
    # endpoint, and assert that it has the correct status. Also assert Event B
    # is still upcoming, since it has not yet broadcast.
    with freeze_time(LAMetroEvent._time_from_now(hours=1)):
        mock_response.json.return_value = []

        assert test_event_a.has_passed
        assert not any([test_event_a.is_upcoming, test_event_a.is_ongoing])

        assert test_event_b.is_upcoming
        assert not any([test_event_b.is_ongoing, test_event_b.has_passed])


def test_check_current_meeting():
    ...


def get_event_id():
    return 'ocd-event/{}'.format(str(uuid4()))


@pytest.mark.parametrize('n_before_board', [1, 4, 8])
def test_upcoming_committee_meetings(event, n_before_board):
    board_date = LAMetroEvent._time_from_now(days=7).strftime('%Y-%m-%d %H:%M')

    board_meeting = event.build(
        name='Regular Board Meeting',
        start_date=board_date,
        id=get_event_id()
    )

    before_board_date = LAMetroEvent._time_from_now(days=6).strftime('%Y-%m-%d %H:%M')
    after_board_date = LAMetroEvent._time_from_now(days=8).strftime('%Y-%m-%d %H:%M')

    # Create ten test meetings.
    for i in range(1, 11):
        if i < n_before_board:
            start_date = before_board_date

        elif i == n_before_board:
            # Create one meeting with the same start date as the board meeting
            # so we can test the board meeting is ordered last.
            start_date = board_date

        else:
            start_date = after_board_date

        event.build(
            name='Test Committee',
            start_date=start_date,
            id=get_event_id()
        )

    upcoming_meetings = LAMetroEvent.upcoming_committee_meetings()

    # Expected behavior: Return at minimum five meetings, up to/including the
    # next board meeting.

    if n_before_board + 1 < 5:
        # The index of the board meeting should be the cardinal number of
        # meetings before the board due to zero-indexing, e.g.,
        # [committee, board, committee, committee, committee]
        assert upcoming_meetings[n_before_board] == board_meeting
        expected_count = 5

    else:
        assert upcoming_meetings.last() == board_meeting
        expected_count = n_before_board + 1

    assert upcoming_meetings.count() == expected_count


def test_upcoming_board_meetings(event):
    one_minute_from_now = LAMetroEvent._time_from_now(minutes=1).strftime('%Y-%m-%d %H:%M')
    forty_days_ago = LAMetroEvent._time_ago(days=40).strftime('%Y-%m-%d %H:%M')
    forty_days_from_now = LAMetroEvent._time_from_now(days=40).strftime('%Y-%m-%d %H:%M')

    # Create a past meeting
    past_board_meeting = event.build(
        name='Regular Board Meeting',
        start_date=forty_days_ago,
        id=get_event_id()
    )

    # Create some meetings for the current date, i.e., upcoming meetings
    upcoming_board_meeting = event.build(
        name='Regular Board Meeting',
        start_date=one_minute_from_now,
        id=get_event_id()
    )
    upcoming_special_board_meeting = event.build(
        name='Special Board Meeting',
        start_date=one_minute_from_now,
        id=get_event_id()
    )
    upcoming_committee_meeting = event.build(
        name='Committee Meeting',
        start_date=one_minute_from_now,
        id=get_event_id()
    )

    # Create a future meeting
    future_board_meeting = event.build(
        name='Regular Board Meeting',
        start_date=forty_days_from_now,
        id=get_event_id()
    )

    upcoming_meetings = LAMetroEvent.upcoming_board_meetings()

    assert upcoming_meetings.count() == 2

    for meeting in (upcoming_board_meeting, upcoming_special_board_meeting):
        assert meeting in upcoming_meetings

    for meeting in (past_board_meeting, upcoming_committee_meeting, future_board_meeting):
        assert meeting not in upcoming_meetings


def test_event_is_upcoming(event, mocker):
    mock_streaming_meetings(mocker)

    in_an_hour = LAMetroEvent._time_from_now(hours=1)

    # Build an event that starts in an hour
    test_event = event.build(start_date=in_an_hour.strftime('%Y-%m-%d %H:%M'))

    # Create three timestamps to test upcoming at three points in time...
    yesterday = (in_an_hour - timedelta(days=1)).date()
    tomorrow = (in_an_hour + timedelta(days=1)).date()

    # Before the upcoming window
    yesterday_afternoon = datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0)

    # During the upcoming window
    yesterday_evening = datetime(yesterday.year, yesterday.month, yesterday.day, 17, 0)

    # After the upcoming window
    tomorrow_morning = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0)

    with freeze_time(yesterday_afternoon):
        assert not test_event.is_upcoming

    with freeze_time(yesterday_evening):
        assert test_event.is_upcoming

        # Test that cancelled meetings are not upcoming, even during the window
        test_event.status = 'cancelled'
        test_event.save()

        assert not test_event.is_upcoming

        test_event.status = 'confirmed'
        test_event.extras['has_broadcast'] = True
        test_event.save()

    with freeze_time(tomorrow_morning):
        assert not test_event.is_upcoming


@freeze_time("2021-02-01 10:00:00")
def test_first_of_month_returns_no_recent_past_meetings(event):
    yesterday = LAMetroEvent._time_ago(days=1).strftime('%Y-%m-%d %H:%M')
    yesterdays_event = event.build(
        name='Board Meeting', start_date=yesterday, id=get_event_id())

    assert len(LAMetroEvent.most_recent_past_meetings()) == 0


@freeze_time("2021-02-07 10:00:00")
def test_most_recent_past_meetings(event):
    three_weeks_ago = LAMetroEvent._time_ago(
        days=21).strftime('%Y-%m-%d %H:%M')
    eight_days_ago_last_month = LAMetroEvent._time_ago(
        days=8).strftime('%Y-%m-%d %H:%M')
    five_days_ago = LAMetroEvent._time_ago(days=5).strftime('%Y-%m-%d %H:%M')
    four_days_ago = LAMetroEvent._time_ago(days=4).strftime('%Y-%m-%d %H:%M')

    earlier_today = LAMetroEvent._time_ago(
        minutes=120).strftime('%Y-%m-%d %H:%M')
    one_hour_from_now = LAMetroEvent._time_from_now(
        minutes=60).strftime('%Y-%m-%d %H:%M')

    one_week_from_now = LAMetroEvent._time_from_now(
        days=7).strftime('%Y-%m-%d %H:%M')

    # Events that shouldn't be returned
    event_older_than_two_weeks = event.build(
        name='Board Meeting', start_date=three_weeks_ago, id=get_event_id())
    event_later_today = event.build(
        name='Board Meeting', start_date=one_hour_from_now, id=get_event_id())
    event_one_week_from_now = event.build(
        name='Board Meeting', start_date=one_week_from_now, id=get_event_id())
    event_last_month = event.build(
        name='Board Meeting', start_date=eight_days_ago_last_month, id=get_event_id())

    # Events that should be returned
    event_earlier_today = event.build(
        name='Board Meeting', start_date=earlier_today, id=get_event_id())
    event_four_days_ago = event.build(
        name='Board Meeting', start_date=four_days_ago, id=get_event_id())
    event_five_days_ago = event.build(
        name='Board Meeting', start_date=five_days_ago, id=get_event_id())

    recent_past_meetings = LAMetroEvent.most_recent_past_meetings()

    assert len(recent_past_meetings) == 3

    assert event_older_than_two_weeks not in recent_past_meetings
    assert event_later_today not in recent_past_meetings
    assert event_one_week_from_now not in recent_past_meetings
    assert event_last_month not in recent_past_meetings

    assert event_four_days_ago in recent_past_meetings
    assert event_five_days_ago in recent_past_meetings
    assert event_earlier_today in recent_past_meetings


def test_todays_meetings(event):
    # create event for some day
    event_time = app_timezone.localize(datetime(2020, 3, 15, 15, 0, 0, 0)) # March 15, 2020 at 3pm LA time

    time_string = event_time.strftime('%Y-%m-%d %H:%M')

    e = event.build(start_date=time_string)

    day_before = event_time - timedelta(days=1)
    with freeze_time(day_before):
        assert e not in LAMetroEvent.todays_meetings()

    with freeze_time(event_time):
        assert e in LAMetroEvent.todays_meetings()


@pytest.mark.parametrize('event_name', [
    ('Regular Board Meeting'),
    ('Finance, Budget and Audit Committee')
])
def test_delete_button_shows(event, admin_client, django_user_model, mocker, event_name):
    e = event.build(name=event_name)
    event_template = reverse('lametro:events', args=[e.slug])

    api_source = f'http://webapi.legistar.com/v1/metro/events/{e.slug}'

    mock_source = mocker.MagicMock()
    mock_source.url = api_source
    mock_api_source = mocker.patch(
        'lametro.models.LAMetroEvent.api_source',
        new_callable=mocker.PropertyMock,
        return_value=mock_source
    )

    source_matcher = re.compile(api_source)
    cal_matcher = re.compile('https://metro.legistar.com/calendar.aspx')
    running_events_matcher = re.compile('http://metro.granicus.com/running_events.php')

    delete_button_text = ('This event does not exist in Legistar. It may have '
                          'been deleted from Legistar due to being a duplicate. '
                          'To delete this event, click the button below.')

    with requests_mock.Mocker() as m:
        m.get(running_events_matcher, status_code=302)
        m.get(cal_matcher, status_code=200)

        m.get(source_matcher, status_code=200, json={'EventBodyName': 'Planning and Programming Committee'})
        response = admin_client.get(event_template)
        assert delete_button_text in response.content.decode('utf-8')

        if event_name == 'Regular Board Meeting':
            api_event_name = 'Board of Directors - Regular Board Meeting'
        else:
            api_event_name = event_name

        m.get(source_matcher, status_code=200, json={'EventBodyName': api_event_name})
        response = admin_client.get(event_template)
        assert delete_button_text not in response.content.decode('utf-8')

        m.get(source_matcher, status_code=404)
        response = admin_client.get(event_template)
        assert delete_button_text in response.content.decode('utf-8')


@pytest.mark.django_db
def test_delete_event(event, client, admin_client):
    e = event.build()
    e.save()
    event_in_db = LAMetroEvent.objects.filter(id=e.id)
    assert event_in_db.exists()

    delete_event = reverse('delete_event', args=[e.slug])
    admin_redirect_url = reverse('lametro:event')

    user_response = client.get(delete_event)
    assert user_response.url != admin_redirect_url
    assert event_in_db.exists()

    admin_response = admin_client.get(delete_event)
    assert admin_response.url == admin_redirect_url

    event_in_db = LAMetroEvent.objects.filter(id=e.id)
    assert not event_in_db.exists()


def test_private_event(client, event, event_location):
    location = event_location.build()
    private_event = event.build()
    private_event.location = location
    private_event.save()

    url = reverse('lametro:events', args=[private_event.slug])
    response = client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_meeting_stream_link_unavailable(mocker):
    '''
    Check that an empty queryset is returned if external site for retrieving meeting stream links is unavailable.
    '''
    mock_response = mocker.MagicMock(spec=requests.Response)
    mock_response.status_code = 404
    mocker.patch('lametro.models.requests.get')

    current_meeting = LAMetroEvent.current_meeting()

    assert isinstance(current_meeting, QuerySet)
    assert len(current_meeting) == 0


@pytest.mark.parametrize('event_name,expected_live_comment_value', [
    ('Special Operations, Safety, and Customer Experience Committee', True),
    ('Planning and Programming Committee', True),
    ('Operations, Safety, and Customer Experience Committee', True),
    ('Finance, Budget and Audit Committee', True),
    ('Executive Management Committee', True),
    ('Construction Committee', True),
    ('Measure R Independent Taxpayer Oversight Committee', False),
    ('Measure M Independent Taxpayer Oversight Committee', False),
    ('Independent Citizen’s Advisory and Oversight Committee', False),
])
def test_live_comment_info_displays_appropriately(client,
                                                  event,
                                                  event_document,
                                                  event_name,
                                                  expected_live_comment_value):

    in_an_hour = LAMetroEvent._time_from_now(hours=1).strftime('%Y-%m-%d %H:%M')
    test_event = event.build(name=event_name, start_date=in_an_hour)
    event_document.build(note='Agenda', event_id=test_event.id)

    assert test_event.accepts_live_comment == expected_live_comment_value

    url = reverse('lametro:events', args=[test_event.slug])
    response = client.get(url)
    response_content = response.content.decode('utf-8')

    live_comment_signature = (
        'During the meeting',
        'By phone:',
        'You may join the public comment participation call 5 minutes prior to the start of the meeting.',
    )

    for line in live_comment_signature:
        assert (line in response_content) == expected_live_comment_value
