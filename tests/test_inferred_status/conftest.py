from datetime import timedelta
import pytest
from django.utils import timezone


@pytest.fixture
def first_event_date():
    return (timezone.now() - timedelta(weeks=2)).strftime("%Y-%m-%d")


@pytest.fixture
def board_event_date():
    return (timezone.now() - timedelta(days=8)).strftime("%Y-%m-%d")


@pytest.fixture
def second_event_date():
    return (timezone.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")


@pytest.fixture
def first_org(metro_organization):
    return metro_organization.build(
        name="Projects and Planning Committee",
        slug="projects-and-planning",
    )


@pytest.fixture
def second_org(metro_organization):
    return metro_organization.build(
        name="Executive Management Committee",
        slug="executive-management-committee",
    )


@pytest.fixture
def first_agenda_item(
    event,
    event_agenda_item,
    event_participant,
    metro_organization,
    first_org,
    first_event_date,
):

    evt = event.build(
        name=first_org.name,
        start_date="{} 12:00".format(first_event_date),
        id="ocd-event/" + first_org.slug,
    )

    event_participant.build(event=evt, organization=first_org)

    return event_agenda_item.build(event=evt)


@pytest.fixture
def second_agenda_item(
    event,
    event_agenda_item,
    event_participant,
    metro_organization,
    second_event_date,
    second_org,
):

    evt = event.build(
        name=second_org.name,
        start_date="{} 12:00".format(second_event_date),
        id="ocd-event/" + second_org.slug,
    )

    event_participant.build(event=evt, organization=second_org)

    return event_agenda_item.build(event=evt)


@pytest.fixture
def board_org(metro_organization):
    return metro_organization.build(
        name="Board of Directors",
        slug="board-of-directors",
    )


@pytest.fixture
def approved_board_agenda_item(
    event, event_agenda_item, event_participant, board_org, board_event_date
):
    evt = event.build(
        name="Regular Board Meeting",
        start_date="{} 12:00".format(board_event_date),
        id="ocd-event/board_mtg_approved",
        extras={"approved_minutes": True},
    )

    event_participant.build(event=evt, organization=board_org)

    return event_agenda_item.build(event=evt)


@pytest.fixture
def unapproved_board_agenda_item(
    event, event_agenda_item, event_participant, board_org, board_event_date
):
    evt = event.build(
        name="Regular Board Meeting",
        start_date="{} 12:00".format(board_event_date),
        id="ocd-event/board_mtg_unapproved",
        extras={"approved_minutes": False},
    )

    event_participant.build(event=evt, organization=board_org)

    return event_agenda_item.build(event=evt)
