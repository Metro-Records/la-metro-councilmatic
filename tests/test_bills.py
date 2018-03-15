import pytest

from django.core.urlresolvers import reverse

from councilmatic_core.models import Bill, RelatedBill

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
