import pytest

from lametro.services import EventService
from opencivicdata.legislative.models import BillVersion


@pytest.mark.django_db
def test_get_related_board_reports_excludes_restricted_bills(
    bill,
    bill_action,
    event_related_entity,
    first_org,
    first_event,
    first_event_date,
    first_agenda_item,
):
    """
    Exclude restricted bills.
    """
    restricted_bill = bill.build(extras={"restrict_view": True})

    BillVersion.objects.create(
        bill=restricted_bill,
        note="Board Report",
        date=first_event_date,
    )

    bill_action.build(
        bill=restricted_bill,
        organization=first_org,
        date=first_event_date,
        order=1,
        description="Don't look at me",
    )

    event_related_entity.build(agenda_item=first_agenda_item, bill=restricted_bill)

    qs = EventService.get_related_board_reports(first_event)
    agenda_items = list(qs)
    assert agenda_items == []


@pytest.mark.django_db
def test_get_related_board_reports_excludes_bills_with_no_BillVersion(
    bill,
    bill_action,
    event_related_entity,
    first_org,
    first_event,
    first_event_date,
    first_agenda_item,
):
    """
    Exclude bills without a BillVersion. May be sign of incomplete import.
    """
    restricted_bill = bill.build()

    bill_action.build(
        bill=restricted_bill,
        organization=first_org,
        date=first_event_date,
        order=1,
        description="Don't look at me",
    )

    event_related_entity.build(agenda_item=first_agenda_item, bill=restricted_bill)

    qs = EventService.get_related_board_reports(first_event)
    agenda_items = list(qs)
    assert agenda_items == []


@pytest.mark.django_db
def test_only_annotates_events_with_actions(
    first_event,
    first_org,
    first_event_date,
    first_agenda_item,
    first_agenda_item_order_2,
    bill,
    bill_action,
    event_related_entity,
):
    """
    Test that LABillManager.with_event_action_description() only
    annotates bills with actions, and returns None for bills with no
    actions, as called by EventService.get_related_board_reports(event).

    This incidentally also tests that agenda items are returned in the
    right order as we access the returned agenda_items by index and
    they are in the order we expect.
    """

    bill_with_action = bill.build()
    BillVersion.objects.create(
        bill=bill_with_action,
        note="Board Report",
        date=first_event_date,
    )
    bill_with_no_action = bill.build()
    BillVersion.objects.create(
        bill=bill_with_no_action,
        note="Board Report",
        date=first_event_date,
    )

    bill_action.build(
        bill=bill_with_action,
        organization=first_org,
        date=first_event_date,
        order=1,
        description="Pick me",
    )

    agenda_item_with_bill_action = first_agenda_item
    agenda_item_with_no_bill_action = first_agenda_item_order_2

    event_related_entity.build(
        agenda_item=agenda_item_with_bill_action, bill=bill_with_action
    )
    event_related_entity.build(
        agenda_item=agenda_item_with_no_bill_action, bill=bill_with_no_action
    )

    qs = EventService.get_related_board_reports(first_event)
    agenda_items = list(qs)

    agenda_item_with_description = agenda_items[0]
    agenda_item_with_no_description = agenda_items[1]

    assert (
        agenda_item_with_description.related_entities.all()[
            0
        ].bill.event_action_description
        == "Pick me"
    )
    assert (
        agenda_item_with_no_description.related_entities.all()[
            0
        ].bill.event_action_description
        is None
    )


@pytest.mark.django_db
def test_annotates_latest_action_when_multiple_actions_with_the_same_date(
    first_org,
    first_event,
    first_event_date,
    first_agenda_item,
    bill,
    bill_action,
    event_related_entity,
):
    """
    Test that annotation is the action with highest order if there
    are multiple actions from the same event.
    """

    bill = bill.build()
    BillVersion.objects.create(
        bill=bill,
        note="Board Report",
        date=first_event_date,
    )

    bill_action.build(
        bill=bill,
        organization=first_org,
        date=first_event_date,
        order=1,
        description="Don't pick me",
    )

    bill_action.build(
        bill=bill,
        organization=first_org,
        date=first_event_date,
        order=2,
        description="Pick me",
    )

    event_related_entity.build(agenda_item=first_agenda_item, bill=bill)

    qs = EventService.get_related_board_reports(first_event)
    agenda_items = list(qs)

    assert (
        agenda_items[0].related_entities.all()[0].bill.event_action_description
        == "Pick me"
    )
