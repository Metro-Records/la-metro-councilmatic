import json

from django.urls import reverse
import pytest
import requests

from lametro.models import LAMetroEvent


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


def test_fetch_subjects_from_related_terms(client, metro_subject):
    subject = metro_subject.build()

    dummy_terms = [subject.name, "some other subject"]

    response = client.get(
        "/subjects/", {"related_terms[]": [subject.name, "some other subject"]}
    )
    response = json.loads(response.content.decode("utf-8"))

    assert response["status_code"] == 200
    assert response["related_terms"] == dummy_terms
    assert response["subjects"] == [subject.name]


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
