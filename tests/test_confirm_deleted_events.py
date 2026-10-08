import pytest
import requests_mock
from uuid import uuid4
from django.core.management import call_command


@pytest.fixture
def deleted_events(event):
    """
    Create a set of events and test events to be checked by confirm_deleted_events
    """

    def build(n_deleted, n_test):
        event_ids = [uuid4() for _ in range(0, n_deleted)]
        events = [
            event.build(id="ocd-event/{}".format(id), slug=id) for id in event_ids
        ]

        test_event_ids = [uuid4() for _ in range(0, n_test)]
        test_events = [
            event.build(id="ocd-event/{}".format(id), slug=id, name="test event")
            for id in test_event_ids
        ]
        return events + test_events

    return build


@pytest.fixture
def request_mocks(monkeypatch):
    with requests_mock.Mocker() as m:
        m.get("https://webapi.legistar.com/v1/metro/bodytypes", status_code=200)
        m.get("https://api.url.fake/?token=test-key", status_code=404)
        m.get("https://api.url.good/?token=test-key", status_code=200)

        monkeypatch.setattr("django.conf.settings.LEGISTAR_TOKEN", "test-key")

        yield m


@pytest.mark.usefixtures("request_mocks")
class TestConfirmDeletedEvents:

    def test_deleted_events_are_marked(self, event_source, event):

        deleted_event = event.build()
        event_source.build(event=deleted_event, note="web", url="url.fake")
        event_source.build(event=deleted_event, note="api", url="https://api.url.fake")

        not_deleted_event = event.build(id="good_event")
        event_source.build(event=not_deleted_event, note="web", url="url.fake")
        event_source.build(
            event=not_deleted_event, note="api", url="https://api.url.good"
        )

        call_command("confirm_deleted_events")
        deleted_event.refresh_from_db()
        not_deleted_event.refresh_from_db()
        assert deleted_event.extras["deleted_in_legistar"] is True
        assert not_deleted_event.extras.get("deleted_in_legistar") is None

    @pytest.mark.parametrize(
        "deleted, test, max",
        [
            (11, 1, ""),  # non-tests greater than max of 10
            (16, 0, "15"),  # non-tests greater than new max
        ],
    )
    def test_confirm_deleted_events_triggers_failsafe(
        self, event_source, deleted, test, max, deleted_events
    ):

        all_events = deleted_events(deleted, test)

        for e in all_events:
            event_source.build(event=e, note="api", url="https://api.url.fake")

        with pytest.raises(Exception, match="Failsafe"):
            if max:
                call_command("confirm_deleted_events", max=int(max))
            else:
                call_command("confirm_deleted_events")

    @pytest.mark.parametrize(
        "deleted, test, max",
        [
            (1, 11, ""),  # tests greater than max
            (5, 6, ""),  # total greater than max
            (0, 16, "15"),  # tests greater than new max
        ],
    )
    def test_confirm_deleted_events_does_not_trigger_failsafe(
        self, event_source, deleted, test, max, deleted_events
    ):

        all_events = deleted_events(deleted, test)

        for e in all_events:
            event_source.build(event=e, note="api", url="https://api.url.fake")

        if max:
            call_command("confirm_deleted_events", max=int(max))
        else:
            call_command("confirm_deleted_events")

        for e in all_events:
            e.refresh_from_db()
            assert e.extras["deleted_in_legistar"]
