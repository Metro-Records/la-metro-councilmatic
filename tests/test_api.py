import json
import os

from django.urls import reverse
import pytest
import requests

from lametro.models import LAMetroEvent
from lametro.api import SmartLogicAPI
from smartlogic.views import SmartLogic


def _test_redirect(response, expected_location):
    (redirect,) = response.redirect_chain

    redirect_url, redirect_status_code = redirect

    assert redirect_status_code == 302
    assert redirect_url == expected_location


@pytest.mark.django_db
def test_public_comment_endpoint_no_meeting(client):
    response = client.get(reverse("lametro:public_comment"), follow=True)
    _test_redirect(response, LAMetroEvent.GENERIC_ECOMMENT_URL)


@pytest.mark.django_db
def test_public_comment_endpoint_one_meeting(
    concurrent_current_meetings, mocker, client
):
    dummy_guid = "a super special guid"
    ecomment_url = "https://ecomment.url"

    # Add dummy GUID to one of our events.
    live_meeting, _ = concurrent_current_meetings

    live_meeting.extras = {
        "guid": dummy_guid.upper(),  # GUIDs in the Legistar API are all caps.
        "ecomment": ecomment_url,
    }

    live_meeting.save()

    # Patch running events endpoint to return our dummy GUID.
    mock_response = mocker.MagicMock(spec=requests.Response)
    mock_response.json.return_value = [
        dummy_guid
    ]  # GUIDs in running events endpoint are all lowercase.
    mock_response.status_code = 200

    mocker.patch("lametro.models.requests.get", return_value=mock_response)

    response = client.get(reverse("lametro:public_comment"), follow=True)
    _test_redirect(response, ecomment_url)


@pytest.mark.django_db
def test_public_comment_endpoint_concurrent_meetings(
    concurrent_current_meetings, client
):
    response = client.get(reverse("lametro:public_comment"), follow=True)
    _test_redirect(response, LAMetroEvent.GENERIC_ECOMMENT_URL)


def _mock_smartlogic(mocker, fixture_file):
    file_directory = os.path.dirname(__file__)
    absolute_file_directory = os.path.abspath(file_directory)
    fixture_path = os.path.join(absolute_file_directory, "fixtures", fixture_file)

    with open(fixture_path, "r") as f:
        concepts = json.load(f)

    mocker.patch.object(SmartLogicAPI, "get_queryset", return_value=concepts)
    mocker.patch.object(SmartLogic, "token", return_value={"access_token": "foo"})


def test_lametro_smartlogic_api_suggest(client, metro_subject, mocker):
    _mock_smartlogic(mocker, "suggest_concepts.json")

    red_line = metro_subject.build(
        name="Metro Red Line",
        guid="1031d836-2d8b-4c20-b3c1-1487f0d503e6",
    )

    rail_operations = metro_subject.build(
        name="Rail Operations - Red Line (Project)",
        guid="b53296db-4ac2-455d-9942-2bfba6f1c8bf",
    )

    lametro_ses_endpoint = reverse(
        "lametro_ses_endpoint", kwargs={"term": "red line", "action": "suggest"}
    )

    response = client.get(lametro_ses_endpoint).json()

    assert response["status_code"] == 200
    assert len(response["subjects"]) == 10

    # Test that the red line is the first result
    assert response["subjects"][0]["guid"] == red_line.guid

    # Test that the synonym matching the search term was appended to the subject name
    assert response["subjects"][0]["display_name"] == "Metro Red Line (Red Line)"


def test_lametro_smartlogic_api_relate(client, metro_subject, mocker):
    _mock_smartlogic(mocker, "relate_concepts.json")

    b_line = metro_subject.build(
        name="Metro Rail B Line", guid="48ddb0c1-2e4a-48c3-adde-74d6dbaaec3f"
    )

    lametro_ses_endpoint = reverse(
        "lametro_ses_endpoint", kwargs={"term": "metro red line", "action": "relate"}
    )

    response = client.get(lametro_ses_endpoint).json()

    assert response["status_code"] == 200
    assert len(response["subjects"]) == 1


@pytest.mark.django_db
def test_fetch_object_counts(client, bill, event):
    bill.build(classification=["Board Box"])
    event.build()

    response = client.get("/object-counts/1").json()

    assert response["status_code"] == 401

    response = client.get("/object-counts/test api key").json()

    assert response["status_code"] == 200
    assert response["bill_count"] == 1
    assert response["event_count"] == 1
