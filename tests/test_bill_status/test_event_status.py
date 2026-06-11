import pytest
from lametro.services import EventService
from opencivicdata.legislative.models import BillVersion


@pytest.mark.django_db
def test_event_action_description(
    first_event,
    first_org,
    first_event_date,
    first_agenda_item,
    bill,
    bill_action,
    event_related_entity,
):
    """
    Test event action description only annotates bill with actions.
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

    event_related_entity.build(agenda_item=first_agenda_item, bill=bill_with_action)
    event_related_entity.build(agenda_item=first_agenda_item, bill=bill_with_no_action)

    qs = EventService.get_related_board_reports(first_event)
    agenda_items = list(qs)
    bill_with_action_result = (
        agenda_items[0].related_entities.get(bill=bill_with_action).bill
    )
    bill_with_no_action_result = (
        agenda_items[0].related_entities.get(bill=bill_with_no_action).bill
    )

    assert bill_with_action_result.event_action_description == "Pick me"
    assert bill_with_no_action_result.event_action_description is None
