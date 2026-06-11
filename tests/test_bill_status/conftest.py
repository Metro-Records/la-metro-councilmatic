from datetime import timedelta
import pytest
from django.utils import timezone

# Set event dates
# 2 weeks ago: first event
# 8 days ago: board meeting
# 7 days ago: second event


@pytest.fixture
def first_event_date():
    return (timezone.now() - timedelta(weeks=2)).strftime("%Y-%m-%d")


@pytest.fixture
def board_event_date():
    return (timezone.now() - timedelta(days=8)).strftime("%Y-%m-%d")


@pytest.fixture
def second_event_date():
    return (timezone.now() - timedelta(weeks=1)).strftime("%Y-%m-%d")


# Create orgs


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
def board_org(metro_organization):
    return metro_organization.build(
        name="Board of Directors",
        slug="board-of-directors",
    )


# Create events


@pytest.fixture
def first_event(event, first_event_date, first_org):
    return event.build(
        name=first_org.name,
        start_date="{} 12:00".format(first_event_date),
        id="ocd-event/" + first_org.slug,
        status="passed",
    )


@pytest.fixture
def second_event(event, second_event_date, second_org):
    return event.build(
        name=second_org.name,
        start_date="{} 12:00".format(second_event_date),
        id="ocd-event/" + second_org.slug,
    )


@pytest.fixture
def another_first_event(event, second_event_date, first_org):
    return event.build(
        name=first_org.name,
        start_date="{} 12:00".format(second_event_date),
        id="ocd-event/another-" + first_org.slug,
    )


@pytest.fixture
def approved_board_event(event, board_event_date, board_org):
    return event.build(
        name=board_org.name,
        start_date="{} 12:00".format(board_event_date),
        id="ocd-event/approved-" + board_org.slug,
        extras={"approved_minutes": True},
    )


@pytest.fixture
def unapproved_board_event(event, board_event_date, board_org):
    return event.build(
        name=board_org.name,
        start_date="{} 12:00".format(board_event_date),
        id="ocd-event/unapproved-" + board_org.slug,
        extras={"approved_minutes": False},
    )


# Create agenda items and event participants

# At the moment, participant objects don't need to be exposed, so just
# do it as side effect of agenda item creation


@pytest.fixture
def first_agenda_item(
    event_agenda_item,
    event_participant,
    first_org,
    first_event,
):

    event_participant.build(event=first_event, organization=first_org)
    return event_agenda_item.build(event=first_event)


@pytest.fixture
def first_agenda_item_order_2(
    event_agenda_item,
    first_org,
    first_event,
):

    return event_agenda_item.build(event=first_event, order=2)


@pytest.fixture
def second_agenda_item(
    event_agenda_item,
    event_participant,
    second_org,
    second_event,
):

    event_participant.build(event=second_event, organization=second_org)
    return event_agenda_item.build(event=second_event)


@pytest.fixture
def approved_board_agenda_item(
    event_agenda_item,
    event_participant,
    board_org,
    approved_board_event,
):

    event_participant.build(event=approved_board_event, organization=board_org)
    return event_agenda_item.build(event=approved_board_event)


@pytest.fixture
def unapproved_board_agenda_item(
    event_agenda_item,
    event_participant,
    board_org,
    unapproved_board_event,
):

    event_participant.build(event=unapproved_board_event, organization=board_org)
    return event_agenda_item.build(event=unapproved_board_event)
