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


    current = subject.build()
    subject_info = { 'id': randrange(10000), 'subject': 'Metro Purple Line', 'bill': current.bill }
    other_subject = subject.build(**subject_info)

    s_g = { 'id': randrange(10000), 'name': current.subject, 'guid': guid }
    new_subject_guid = { 'id': randrange(10000), 'name': new_subject.subject, 'guid': guid }


    current_subject_guid = subject_guid.build(current)
    other_subject_guid = subject_guid.build(**new_subject_guid)

    response = client.get('/topic/', { 'guid': guid })
    assert response.status_code == 200








# def test_fetch_multiple_topics():
# def test_fetch_no_topics():
