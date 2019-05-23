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

    canonical_subject = subject.build()

    canonical_subject_guid_info = { 'name': canonical_subject.subject }
    old_subject_guid_info = {'name': 'Old Subject'}

    canonical_subject_guid = subject_guid.build(**canonical_subject_guid_info)
    old_subject_guid = subject_guid.build(**old_subject_guid_info)

    response = client.get('/topic/', { 'guid': canonical_subject_guid.guid })
    assert response.status_code == 200

# def test_fetch_no_topics(client, subject_guid):
#
#     guid = '0000-4-0000'
#     response = client.get('/topic/', { 'guid': guid })
#
#     assert response.status_code == 404
