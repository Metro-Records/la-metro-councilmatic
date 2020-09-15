from datetime import timedelta
from uuid import uuid4

import pytest

from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from opencivicdata.legislative.models import EventAgendaItem, RelatedBill
from councilmatic_core.models import Bill, Event
from lametro.models import LAMetroBill
from lametro.utils import format_full_text, parse_subject


# This collection of tests checks the functionality of Bill-specific views, helper functions, and relations.
def test_bill_url(client, bill):
    '''
    This test checks that the bill detail view returns a successful response.
    '''
    bill = bill.build()
    url = reverse('bill_detail', kwargs={'slug': bill.slug})
    response = client.get(url)

    assert response.status_code == 200

def test_related_bill_relation(client, bill):
    '''
    This test checks that the related_bill relation works as expected.
    '''
    central_bill = bill.build()

    related_bill_info = {
        'id': 'ocd-bill/8b90f9f4-1421-4450-a34e-766ca2f8be26',
        'title': 'RECEIVE AND FILE the Draft Measure M Project Acceleration/Deceleration Factors and Evaluation Process',
        'updated_at': '2017-07-26 11:06:47.1853',
        'identifier': '2017-0596',
        'classification': ['Report'],
        'slug': '2017-0596'
    }

    related_bill = bill.build(**related_bill_info)

    RelatedBill.objects.create(bill=central_bill,
                               related_bill=related_bill)

    assert central_bill.related_bills.count() == 1
    assert central_bill.related_bills.first().related_bill.identifier == '2017-0596'

@pytest.mark.parametrize('text,subject', [
    ("..Subject\nSUBJECT:\tFOOD SERVICE OPERATOR\n\n..Action\nACTION:\tAWARD SERVICES CONTRACT\n\n..", "\tFOOD SERVICE OPERATOR"),
    ("..Subject/Action\r\nSUBJECT: MONTHLY REPORT ON CRENSHAW/LAX SAFETY\r\nACTION: RECEIVE AND FILE\r\n", " MONTHLY REPORT ON CRENSHAW/LAX SAFETY"),
    ("..Subject\nSUBJECT:    REVISED MOTION BY DIRECTORS HAHN, SOLIS,\nGARCIA, AND DUPONT-WALKER\n..Title\n", "    REVISED MOTION BY DIRECTORS HAHN, SOLIS, GARCIA, AND DUPONT-WALKER")
])
def test_format_full_text(bill, text, subject):
    '''
    This test checks that format_full_text correctly parses the subject header.
    '''
    bill_info = {
        'extras': {'plain_text': text}
    }

    bill_with_text = bill.build(**bill_info)

    full_text = bill_with_text.extras['plain_text']

    assert format_full_text(full_text) == subject

@pytest.mark.parametrize('restrict_view,bill_type,event_status,is_public', [
        (True, 'Board Box', 'passed', False),
        (False, 'Board Box', 'passed', True),
        (False, 'Resolution', 'passed', True),
        (False, 'Resolution', 'cancelled', True),
        (False, 'Resolution', 'confirmed', False),
    ])
def test_bill_manager(bill,
                      event_related_entity,
                      restrict_view,
                      bill_type,
                      event_status,
                      is_public):
    '''
    Tests if the LAMetroBillManager properly filters public and private bills.
    Private bills should not be discoverable, i.e., refresh_from_db should fail.
    '''
    extras = {'restrict_view': restrict_view}

    bill_info = {
        'classification': [bill_type],
        'extras': extras,
    }

    some_bill = bill.build(**bill_info)

    event_related_entity_info = {
        'bill': some_bill,
    }

    related_entity = event_related_entity.build(**event_related_entity_info)

    event = related_entity.agenda_item.event
    event.status = event_status
    event.save()

    event.refresh_from_db()
    related_entity.refresh_from_db()

    try:
        some_bill.refresh_from_db()
    except ObjectDoesNotExist:
        assert is_public == False
    else:
        bill_qs_with_manager = LAMetroBill.objects.filter(id=some_bill.id)
        assert is_public == (some_bill in bill_qs_with_manager)

@pytest.mark.django_db
def test_last_action_date_has_already_occurred(bill, event):
    some_bill = bill.build()

    two_weeks_ago = timezone.now() - timedelta(weeks=2)
    two_weeks_from_now = timezone.now() + timedelta(weeks=2)

    id_fmt = 'ocd-event/{}'

    for t in (two_weeks_ago, two_weeks_from_now):
        some_event = event.build(id=id_fmt.format(uuid4()), start_date=t.date())
        item = some_event.agenda.create(order=1)
        item.related_entities.create(bill=some_bill)

    # Assert the bill occurs on both agendas.
    assert Event.objects.filter(agenda__related_entities__bill=some_bill)\
                        .count() == 2

    last_action_date = some_bill.councilmatic_bill.get_last_action_date()

    # Assert the last action matches the event that has already occurred.
    assert last_action_date == two_weeks_ago.date()
