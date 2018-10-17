import pytest

from django.core.urlresolvers import reverse

from councilmatic_core.models import Bill, RelatedBill, Event
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
        'ocd_id': 'ocd-bill/8b90f9f4-1421-4450-a34e-766ca2f8be26',
        'description': 'RECEIVE AND FILE the Draft Measure M Project Acceleration/Deceleration Factors and Evaluation Process', 
        'ocd_created_at': '2017-06-16 14:23:30.970325-05', 
        'ocd_updated_at': '2017-06-16 14:23:30.970325-05', 
        'updated_at': '2017-07-26 11:06:47.1853',
        'identifier': '2017-0596', 
        'slug': '2017-0596' 
    }

    related_bill = bill.build(**related_bill_info)

    RelatedBill.objects.create(related_bill_identifier=related_bill.identifier, 
                               central_bill_id=central_bill.ocd_id)   

    assert central_bill.related_bills.count() == 1
    assert central_bill.related_bills.first().related_bill_identifier == '2017-0596'  

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
        'ocr_full_text': text
    }

    bill_with_text = bill.build(**bill_info)

    full_text = bill_with_text.ocr_full_text

    assert format_full_text(full_text) == subject

@pytest.mark.parametrize('bill_type,event_status,assertion', [
        ('Board Box', 'passed', True),
        ('Resolution', 'passed', True),
        ('Resolution', 'cancelled', True),
        ('Resolution', 'confirmed', False),
    ])
def test_viewable_bill(bill, 
                       event_agenda_item, 
                       bill_type, 
                       event_status, 
                       assertion):
    bill_info = {
        'bill_type': bill_type,
    }
    bill = bill.build(**bill_info)
    bill.refresh_from_db()

    event_agenda_item_info = {
        'bill_id': bill.ocd_id,
    }
    item = event_agenda_item.build(**event_agenda_item_info)
    item.refresh_from_db()

    event = Event.objects.get(ocd_id=item.event_id)
    event.status = event_status
    event.save()
    event.refresh_from_db()

    assert bill.is_viewable == assertion



