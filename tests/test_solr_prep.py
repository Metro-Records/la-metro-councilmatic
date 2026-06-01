import pytest
from datetime import datetime, timedelta

from opencivicdata.legislative.models import EventParticipant

from lametro.search_indexes import LAMetroBillIndex


# Helper function
def patch_aa(mocker, return_value):
    mocker.patch(
        "lametro.models.LAMetroBill.actions_and_agendas",
        new_callable=mocker.PropertyMock,
        return_value=return_value,
    )


@pytest.mark.parametrize("month", [6, 7])
def test_legislative_session(bill, metro_organization, event, mocker, month):
    """
    This test instantiates LAMetroBillIndex – a subclass of SearchIndex from
    Haystack, used for building the Solr index.

    The test, then, calls the SearchIndex `prepare` function,
    which returns a dict of prepped data.
    https://github.com/django-haystack/django-haystack/blob/4910ccb01c31d12bf22dcb000894eece6c26f74b/haystack/indexes.py#L198
    """
    # Set up
    now = datetime.now()
    org = metro_organization.build()
    event = event.build()
    bill = bill.build()
    index = LAMetroBillIndex()

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

    def date_to_fy_string(date):
        """
        Return the correct fiscal year for a given date, June (6) being the last month of the year.
        """
        start_year = date.year - 1 if date.month <= 6 else date.year
        end_year = date.year if date.month <= 6 else date.year + 1
        return "7/1/{0} to 6/30/{1}".format(start_year, end_year)

    # Test indexed value when there are both actions and agendas

    patch_aa(mocker, [recent_action, older_action, recent_agenda, older_agenda])
    indexed_data = index.prepare(bill)
    expected_value = date_to_fy_string(recent_agenda["date"])

    assert indexed_data["legislative_session"] == expected_value

    # Test indexed value when there are just actions

    patch_aa(mocker, [recent_action, older_action])
    indexed_data = index.prepare(bill)
    expected_value = date_to_fy_string(recent_action["date"])

    assert indexed_data["legislative_session"] == expected_value


def test_legislative_session_fallback(bill, metro_organization, event, mocker):
    bill = bill.build()
    event = event.build()
    org = metro_organization.build()
    session = bill.legislative_session
    index = LAMetroBillIndex()
    now = datetime.now()

    single_action = {
        "date": datetime(now.year, 7, 1),
        "description": "action descripton",
        "event": event,
        "organization": org,
    }

    patch_aa(mocker, [single_action])

    indexed_data = index.prepare(bill)
    expected_fmt = "7/1/{0} to 6/30/{1}"
    expected_value = expected_fmt.format(
        session.start_date.split("-")[0], session.end_date.split("-")[0]
    )

    assert indexed_data["legislative_session"] == expected_value

    # Test indexed value when there are neither actions nor agendas

    patch_aa(mocker, [])
    indexed_data = index.prepare(bill)

    assert indexed_data["legislative_session"] == expected_value


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
