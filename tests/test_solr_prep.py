import pytest
from datetime import datetime, timedelta

from opencivicdata.legislative.models import EventParticipant

from lametro.search_indexes import LAMetroBillIndex


@pytest.mark.parametrize("month", [6, 7])
def test_legislative_session(bill, metro_organization, event, mocker, month):
    """
    This test instantiates LAMetroBillIndex – a subclass of SearchIndex from
    Haystack, used for building the Solr index.

    The test, then, calls the SearchIndex `prepare` function,
    which returns a dict of prepped data.
    https://github.com/django-haystack/django-haystack/blob/4910ccb01c31d12bf22dcb000894eece6c26f74b/haystack/indexes.py#L198
    """
    org = metro_organization.build()
    event = event.build()
    bill = bill.build()

    now = datetime.now()

    # Create test actions and agendas
    recent_action = {
        "date": datetime(now.year, month, 1),
        "description": "org2 descripton",
        "event": event,
        "organization": org,
    }
    older_action = {
        "date": datetime(now.year, month, 1) - timedelta(days=365 * 2),
        "description": "org2 descripton",
        "event": event,
        "organization": org,
    }
    recent_agenda = {
        "date": datetime(now.year, month, 1) - timedelta(days=365),
        "description": "SCHEDULED",
        "event": event,
        "organization": org,
    }
    older_agenda = {
        "date": datetime(now.year, month, 1) - timedelta(days=365 * 3),
        "description": "SCHEDULED",
        "event": event,
        "organization": org,
    }

    # Test indexed value when there are both actions and agendas
    mock_actions_and_agendas = mocker.PropertyMock(
        return_value=[recent_action, older_action, recent_agenda, older_agenda]
    )

    mocker.patch(
        "lametro.models.LAMetroBill.actions_and_agendas",
        new_callable=mock_actions_and_agendas,
    )

    index = LAMetroBillIndex()
    expected_fmt = "7/1/{0} to 6/30/{1}"

    indexed_data = index.prepare(bill)

    if month <= 6:
        expected_value = expected_fmt.format(
            recent_agenda["date"].year - 1, recent_agenda["date"].year
        )
    else:
        expected_value = expected_fmt.format(
            recent_agenda["date"].year, recent_agenda["date"].year + 1
        )

    assert indexed_data["legislative_session"] == expected_value

    # Test indexed value when there are just actions
    mock_actions_and_agendas = mocker.PropertyMock(
        return_value=[recent_action, older_action]
    )

    mocker.patch(
        "lametro.models.LAMetroBill.actions_and_agendas",
        new_callable=mock_actions_and_agendas,
    )

    indexed_data = index.prepare(bill)

    if month <= 6:
        expected_value = expected_fmt.format(
            recent_action["date"].year - 1, recent_action["date"].year
        )
    else:
        expected_value = expected_fmt.format(
            recent_action["date"].year, recent_action["date"].year + 1
        )

    assert indexed_data["legislative_session"] == expected_value

    # Test indexed value when there are neither actions nor agendas
    mock_actions_and_agendas = mocker.PropertyMock(return_value=[])

    mocker.patch(
        "lametro.models.LAMetroBill.actions_and_agendas",
        new_callable=mock_actions_and_agendas,
    )

    indexed_data = index.prepare(bill)

    assert not indexed_data["legislative_session"]


def test_sponsorships(bill, metro_organization, event, event_related_entity, mocker):
    bill = bill.build()

    org1 = metro_organization.build()
    org2 = metro_organization.build()
    event1 = event.build()
    event1_participant = EventParticipant.objects.create(
        event=event1, name="Public Hearing"
    )
    actions_and_agendas = [
        {
            "date": datetime.now(),
            "description": "org1 description",
            "event": event1,
            "organization": org1,
        },
        {
            "date": datetime.now(),
            "description": "org2 descripton",
            "event": event1,
            "organization": org2,
        },
        {
            "date": datetime.now(),
            "description": "org2 descripton",
            "event": event1,
            "organization": org2,
        },
        {
            "date": datetime.now(),
            "description": "SCHEDULED",
            "event": event1,
            "organization": event1_participant,
        },
    ]
    mocker.patch(
        "lametro.models.LAMetroBill.actions_and_agendas",
        new_callable=mocker.PropertyMock,
        return_value=actions_and_agendas,
    )

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert indexed_data["sponsorships"] == {org1.name, org2.name, "Public Hearing"}
