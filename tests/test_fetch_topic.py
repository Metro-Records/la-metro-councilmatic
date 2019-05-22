import pytest
import requests

from councilmatic_core.models import Bill, Subject
from lametro.models import SubjectGuid
from lametro.views import fetch_topic

def test_fetch_single_topic(client, subject_guid):
    s_g = subject_guid.build()
    guid = '0000-0-0000'

    response = client.get('/fetch_topic/', { 'guid': guid })
    print(response)
    assert response.status_code == 200








# def test_fetch_multiple_topics():
# def test_fetch_no_topics():
