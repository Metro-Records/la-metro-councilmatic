import pytest
import requests

from random import randrange

from councilmatic_core.models import Bill, Subject
from lametro.models import SubjectGuid
from lametro.views import fetch_topic

def test_fetch_single_topic(client, subject_guid):
    s_g = subject_guid.build()
    guid = '0000-0-0000'

    response = client.get('/topic/', { 'guid': guid })
    assert response.status_code == 200

def test_one_guid_multiple_topics(client, subject_guid, subject, bill):
    guid = '0000-0-0000'

    bill_info = {
        'ocd_id': 'ocd-bill/8b90f9f4-1421-4450-a34e-766ca2f8be26',
        'description': 'RECEIVE AND FILE the Draft Measure M Project Acceleration/Deceleration Factors and Evaluation Process',
        'ocd_created_at': '2017-06-16 14:23:30.970325-05',
        'ocd_updated_at': '2017-06-16 14:23:30.970325-05',
        'updated_at': '2017-07-26 11:06:47.1853',
        'identifier': '2017-0596',
        'slug': '2017-0596'
    }

    new_bill = bill.build(**bill_info)
    subject_info = {'bill': new_bill}
    current = subject.build(**subject_info)
    current_s_g = { 'name': current.subject }
    new_subject_guid = { 'name': 'Metro Purple Line' }

    current_subject_guid = subject_guid.build(**current_s_g)
    other_subject_guid = subject_guid.build(**new_subject_guid)

    response = client.get('/topic/', { 'guid': guid })
    assert response.status_code == 200

# def test_fetch_multiple_topics():

# def test_fetch_no_topics(client, subject_guid):
#
#     guid = '0000-4-0000'
#     response = client.get('/topic/', { 'guid': guid })
#
#     assert response.status_code == 404
