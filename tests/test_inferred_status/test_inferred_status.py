import pytest


@pytest.mark.django_db
def test_inferred_status_no_agendas_or_actions(bill):
    """
    Test inferred status returns empty string if no actions or agendas.
    """
    some_bill = bill.build()

    assert some_bill.inferred_status == ""


@pytest.mark.django_db
def test_inferred_status_one_agenda_no_actions(
    bill, event_related_entity, first_agenda_item
):
    """
    Test inferred status returns empty string if scheduled on one agenda, but no actions.
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=first_agenda_item, bill=some_bill)

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
    Test inferred status with only one meeting type returns current action status.
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

    assert some_bill.inferred_status == "Active"


@pytest.mark.django_db
def test_inferred_status_two_agendas_no_actions(
    bill, event_related_entity, first_agenda_item, second_agenda_item, board_org
):
    """
    Test inferred status returns empty string if scheduled on multiple agendas, but no actions.
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=first_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)

    assert some_bill.inferred_status == ""


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
    Test inferred status returns only "Active" statuses, else "", with two non-board organizations.
    This case was the cause of issue #1278.
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
    Test inferred status returns only "Active" or "" when the board is one of the organizations,
    but the board meeting agenda is not approved.
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=unapproved_board_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        date=second_event_date,
        organization=second_org,
        description=description,
    )

    assert some_bill.inferred_status == expected


@pytest.mark.django_db
def test_inferred_status_two_orgs_including_approved_board_no_board_action(
    bill,
    bill_action,
    event_related_entity,
    second_agenda_item,
    approved_board_agenda_item,
    second_event_date,
    second_org,
    board_org,
):
    """
    Test inferred status returns "" when board meeting minutes are approved but
    the latest action is not from the board.
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=approved_board_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        organization=second_org,
        date=second_event_date,
        description="withdrawn",
    )

    assert some_bill.inferred_status == ""


@pytest.mark.django_db
def test_inferred_status_two_orgs_including_approved_board_yes_board_action(
    bill,
    bill_action,
    event_related_entity,
    second_agenda_item,
    approved_board_agenda_item,
    second_event_date,
    second_org,
    board_event_date,
    board_org,
):
    """
    Test inferred status returns board action status when board meeting minutes are approved
    and there is a board action.
    """
    some_bill = bill.build()
    event_related_entity.build(agenda_item=second_agenda_item, bill=some_bill)
    event_related_entity.build(agenda_item=approved_board_agenda_item, bill=some_bill)

    bill_action.build(
        bill=some_bill,
        date=board_event_date,
        description="approved",
        organization=board_org,
    )
    bill_action.build(
        bill=some_bill,
        date=second_event_date,
        description="withdrawn",
        organization=second_org,
    )

    assert some_bill.inferred_status == "Approved"
