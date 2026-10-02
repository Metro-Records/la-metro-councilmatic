import pytest


@pytest.mark.django_db
def test_inferred_status_no_agendas_or_actions(
    bill, first_agenda_item, second_agenda_item, event_related_entity
):
    """
    Test inferred status returns empty string if no actions,
    given 0, 1, or 1+ agendas.
    """

    some_bill = bill.build()

    assert len(some_bill.actions_and_agendas) == 0
    assert some_bill.inferred_status == ""

    event_related_entity.build(agenda_item=first_agenda_item, bill=some_bill)

    assert len(some_bill.actions_and_agendas) == 1
    assert some_bill.inferred_status == ""

    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)

    assert len(some_bill.actions_and_agendas) == 2
    assert some_bill.inferred_status == ""


@pytest.mark.django_db
def test_inferred_status_one_org_agenda_actions(
    bill,
    bill_action,
    event_related_entity,
    first_agenda_item,
    first_event_date,
    first_org,
    board_org,
):
    """
    Test inferred status returns current action status.
    """
    some_bill = bill.build()

    event_related_entity.build(agenda_item=first_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        date=first_event_date,
        organization=first_org,
        order=1,
        description="received",
    )

    bill_action.build(
        bill=some_bill,
        date=first_event_date,
        organization=first_org,
        order=2,
        description="carried over",
    )

    assert len(some_bill.actions_and_agendas) == 3
    assert some_bill.inferred_status == "Active"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "first_description, second_description, expected",
    [
        ("Withdrawn", "Received", ""),
        ("Carried over", "Withdrawn", ""),
        ("Received", "Carried over", "Active"),
    ],
)
def test_inferred_status_two_orgs_no_board(
    bill,
    bill_action,
    event_related_entity,
    first_agenda_item,
    second_agenda_item,
    first_event_date,
    second_event_date,
    first_description,
    second_description,
    first_org,
    second_org,
    expected,
    board_org,
):
    """
    This case was the cause of issue #1278.

    If the bill appears in two non-board meetings,
    test inferred status returns only "Active" statuses, else "",
    """
    some_bill = bill.build()

    event_related_entity.build(agenda_item=first_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        date=first_event_date,
        organization=first_org,
        description=first_description,
        order=1,
    )
    bill_action.build(
        bill=some_bill,
        date=second_event_date,
        organization=second_org,
        description=second_description,
        order=2,
    )

    assert len(some_bill.actions_and_agendas) == 4
    assert some_bill.inferred_status == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "description, expected",
    [
        ("Withdrawn", ""),
        ("Received", ""),
        ("Forwarded without recommendation", "Active"),
    ],
)
def test_inferred_status_two_orgs_including_unapproved_board(
    bill,
    bill_action,
    event_related_entity,
    second_agenda_item,
    second_org,
    unapproved_board_agenda_item,
    second_event_date,
    description,
    expected,
    board_org,
):
    """
    If the bill appears in a board meeting,
    and the meeting minutes are NOT approved,
    test inferred status returns only "Active" or ""
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=unapproved_board_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        organization=second_org,
        date=second_event_date,
        description=description,
    )

    assert len(some_bill.actions_and_agendas) == 3
    assert some_bill.inferred_status == expected


@pytest.mark.django_db
def test_inferred_status_two_orgs_including_board_meeting_with_approved_minutes(
    bill,
    bill_action,
    event_related_entity,
    second_agenda_item,
    approved_board_agenda_item,
    second_event_date,
    second_org,
    board_org,
    board_event_date,
    recent_board_event_date,
    recent_approved_board_agenda_item,
):
    """
    If a bill appears in a board meeting,
    and the meeting minutes ARE approved:

    1. When the latest action is not from the board,
       test inferred status returns ""

    2. When the latest action is from the board,
       test inferred status returns the matching status

    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=approved_board_agenda_item, bill=some_bill)

    # note that order matters, not actual date
    # see LAMetroBill.action_and_agendas()
    bill_action.build(
        bill=some_bill,
        organization=board_org,
        date=board_event_date,
        description="carried over",
        order=1,
    )

    bill_action.build(
        bill=some_bill,
        organization=second_org,
        date=second_event_date,
        description="withdrawn",
        order=2,
    )

    assert len(some_bill.actions_and_agendas) == 4
    assert some_bill.inferred_status == ""

    event_related_entity.build(
        agenda_item=recent_approved_board_agenda_item, bill=some_bill
    )

    bill_action.build(
        bill=some_bill,
        organization=board_org,
        date=recent_board_event_date,
        description="approved",
        order=3,
    )

    assert len(some_bill.actions_and_agendas) == 6
    assert some_bill.inferred_status == "Approved"
