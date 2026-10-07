from lametro.management.commands.confirm_deleted_events import check_deleted
import requests
import pytest
import requests_mock
from django.core.management import call_command


@pytest.mark.parametrize(
    "ok, expected",
    [
        (True, False),
        (False, True),
    ],
)
def test_check_deleted_returns_correct_values(mocker, ok, expected):
    """
    Return False for existing URLs, True for non-existent URLs
    """

    mock_response = mocker.MagicMock(spec=requests.Response)
    mock_response.ok = ok

    mocker.patch("lametro.models.requests.get", return_value=mock_response)
    assert check_deleted("fake_url") is expected


def test_confirm_deleted_events(event_source, event):
    with requests_mock.Mocker() as m:
        m.get("https://webapi.legistar.com/v1/metro/bodytypes", status_code=200)
        m.get("https://api.url.fake", status_code=404)

        test_event = event.build()
        event_source.build(event=test_event, note="web", url="url.fake")
        event_source.build(event=test_event, note="api", url="https://api.url.fake")

        call_command("confirm_deleted_events")
        test_event.refresh_from_db()
        assert test_event.extras["deleted_in_legistar"] is True


def test_confirm_deleted_events_failsafe(mocker, event_source, event):
    #    createBulkEventsWithSources(10)
    pass
