import pytest
import requests_mock

from django.urls import reverse

from lametro.models import EventAgenda


@pytest.mark.parametrize("legistar_ok", [True, False])
@pytest.mark.parametrize("event_ok", [True, False])
@pytest.mark.parametrize("manual_agenda", [True, False])
@pytest.mark.parametrize("scraped_agenda", [True, False])
def test_event_admin_renders_based_on_context(
    legistar_ok,
    event_ok,
    manual_agenda,
    scraped_agenda,
    mocker,
    event,
    admin_client,
):
    event = event.build()

    dummy_service = mocker.patch("lametro.views.EventService", spec=True)

    assert_consistent_with_api = mocker.MagicMock(return_value=event_ok)
    dummy_service.assert_consistent_with_api = assert_consistent_with_api

    get_agenda = mocker.MagicMock()

    if manual_agenda or scraped_agenda:
        get_agenda.return_value = {
            "url": "agenda url",
            "timestamp": None,
            "manual": manual_agenda and not scraped_agenda,
        }

        if manual_agenda:
            EventAgenda.objects.create(event=event, url="manual agenda url")

    else:
        get_agenda.return_value = None

    dummy_service.get_agenda = get_agenda

    with requests_mock.Mocker() as m:
        m.head(
            "https://metro.legistar.com/calendar.aspx",
            status_code=200 if legistar_ok else 500,
        )
        resp = admin_client.get(reverse("lametro:events", kwargs={"slug": event.slug}))
        page_content = resp.content.decode("utf-8")

    possible_text = [
        "does not detect a Legistar outage",
        "detects a Legistar outage",
        "event does not exist in Legistar",
        "has been scraped",
        "also has a manually uploaded agenda",
        "Click the button below to update or remove it",
        "Upload an agenda",
    ]
    expected_text = []

    def expect_phrase(possible_text, expected_text, phrase):
        assert phrase in possible_text
        possible_text.remove(phrase)
        expected_text.append(phrase)
        return possible_text, expected_text

    if legistar_ok:
        expected_phrase = "does not detect a Legistar outage"
    else:
        expected_phrase = "detects a Legistar outage"

    possible_text, expected_text = expect_phrase(
        possible_text, expected_text, expected_phrase
    )

    if legistar_ok and not event_ok:
        expected_phrase = "event does not exist in Legistar"
        possible_text, expected_text = expect_phrase(
            possible_text, expected_text, expected_phrase
        )

    if scraped_agenda:
        expected_phrase = "has been scraped"
        possible_text, expected_text = expect_phrase(
            possible_text, expected_text, expected_phrase
        )

        if manual_agenda:
            expected_phrase = "also has a manually uploaded agenda"
            possible_text, expected_text = expect_phrase(
                possible_text, expected_text, expected_phrase
            )

    elif manual_agenda:
        expected_phrase = "Click the button below to update or remove it"
        possible_text, expected_text = expect_phrase(
            possible_text, expected_text, expected_phrase
        )

    else:
        expected_phrase = "Upload an agenda"
        possible_text, expected_text = expect_phrase(
            possible_text, expected_text, expected_phrase
        )

    for t in expected_text:
        assert t in page_content

    for t in possible_text:
        assert t not in page_content
