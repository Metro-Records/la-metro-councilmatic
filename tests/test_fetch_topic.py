import pytest
import requests
import json

from random import randrange

from councilmatic_core.models import Bill, Subject
from lametro.models import SubjectGuid
from lametro.views import fetch_topic

def test_fetch_single_topic(client, subject_guid):

    '''
    This tests returning a single Subject matching the GUID
    '''

    s_g = subject_guid.build()

    response = client.get('/topic/', { 'guid': s_g.guid })
    response = json.loads(response.content.decode('utf-8'))
    assert response['status_code'] == 200

def test_one_guid_multiple_topics(client, subject_guid, subject, bill):

    '''
    This tests multiple SubjectGuids matching the GUID, and returning only the correct Subject
    '''

    canonical_subject = subject.build()

    canonical_subject_guid_info = { 'name': canonical_subject.subject }
    old_subject_guid_info = {'name': 'Old Subject'}

    canonical_subject_guid = subject_guid.build(**canonical_subject_guid_info)
    old_subject_guid = subject_guid.build(**old_subject_guid_info)

    response = client.get('/topic/', { 'guid': canonical_subject_guid.guid })
    assert response.status_code == 200

def test_fetch_no_topics(client, subject_guid):

    '''
    This tests that an error is returned when there is no matching SubjectGuid to the GUID
    '''

    response = client.get('/topic/', { 'guid': '0000-5-0000' })
    response = json.loads(response.content.decode('utf-8'))

    assert response['status_code'] == 404
