import pytest
from django.utils import timezone

from lametro.services import EventService
from opencivicdata.legislative.models import BillVersion


@pytest.mark.django_db
def test_event_action_description(
    first_event,
    first_org,
    first_event_date,
    first_agenda_item,
    another_first_agenda_item,
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
    bill_info = {
        "id": "ocd-bill/2436c8c9-564f-4cdd-a2ce-bcfe082de2c2",
        "title": "A unique bill",
        "created_at": timezone.now(),
        "updated_at": timezone.now(),
        "identifier": "2019-0686",
        "slug": "2019-0686",
    }
    bill_with_no_action = bill.build(**bill_info)

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
    agenda_item_with_no_bill_action = another_first_agenda_item

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
