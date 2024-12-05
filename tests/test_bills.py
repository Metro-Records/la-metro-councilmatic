from datetime import timedelta, datetime
import logging
from uuid import uuid4

import pytest

from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from opencivicdata.legislative.models import (
    RelatedBill,
    EventParticipant,
)
from councilmatic_core.models import Event
from lametro.models import LAMetroBill
from lametro.utils import format_full_text


# This collection of tests checks the functionality of Bill-specific views, helper functions, and relations.
def test_bill_url(client, bill):
    """
    This test checks that the bill detail view returns a successful response.
    """
    bill = bill.build()
    bill.classification = ["Board Box"]
    bill.save()
    url = reverse("lametro:bill_detail", kwargs={"slug": bill.slug})
    response = client.get(url)

    assert response.status_code == 200


def test_related_bill_relation(client, bill):
    """
    This test checks that the related_bill relation works as expected.
    """
    central_bill = bill.build()

    related_bill_info = {
        "id": "ocd-bill/8b90f9f4-1421-4450-a34e-766ca2f8be26",
        "title": "RECEIVE AND FILE the Draft Measure M",
        "updated_at": "2017-07-26 11:06:47.1853",
        "identifier": "2017-0596",
        "classification": ["Report"],
        "slug": "2017-0596",
    }

    related_bill = bill.build(**related_bill_info)

    RelatedBill.objects.create(bill=central_bill, related_bill=related_bill)

    assert central_bill.related_bills.count() == 1
    assert central_bill.related_bills.first().related_bill.identifier == "2017-0596"


@pytest.mark.parametrize(
    "text,subject",
    [
        (
            "..Subject\nSUBJECT:\tFOOD SERVICE OPERATOR\n\n..Action\nACTION:\tAWARD SERVICES CONTRACT\n\n..",
            "\tFOOD SERVICE OPERATOR",
        ),
        (
            "..Subject/Action\r\nSUBJECT: MONTHLY REPORT ON CRENSHAW/LAX SAFETY\r\nACTION: RECEIVE AND FILE\r\n",
            " MONTHLY REPORT ON CRENSHAW/LAX SAFETY",
        ),
        (
            "..Subject\nSUBJECT:    REVISED MOTION BY DIRECTORS HAHN, SOLIS,\nGARCIA, AND DUPONT-WALKER\n..Title\n",
            "    REVISED MOTION BY DIRECTORS HAHN, SOLIS, GARCIA, AND DUPONT-WALKER",
        ),
    ],
)
def test_format_full_text(bill, text, subject):
    """
    This test checks that format_full_text correctly parses the subject header.
    """
    bill_info = {"extras": {"plain_text": text}}

    bill_with_text = bill.build(**bill_info)

    full_text = bill_with_text.extras["plain_text"]

    assert format_full_text(full_text) == subject


@pytest.mark.parametrize(
    "restrict_view,bill_type,event_status,has_action,is_public",
    [
        (True, "Board Box", "passed", False, False),  # private bill
        (False, "Board Box", "passed", False, True),  # board box
        (False, "Board Correspondence", "passed", False, True),  # board correspondence
        (False, "Resolution", "passed", False, True),  # on published agenda
        (False, "Resolution", "cancelled", False, True),  # on published agenda
        (False, "Resolution", "confirmed", False, False),  # not on published agenda
        (False, "Resolution", "passed", True, True),  # has matter history
        (
            False,
            "Test",
            "test",
            False,
            False,
        ),  # not private, but does not meet conditions for display
    ],
)
def test_bill_manager(
    bill,
    bill_action,
    event_related_entity,
    restrict_view,
    bill_type,
    event_status,
    has_action,
    is_public,
):
    """
    Tests if the LAMetroBillManager properly filters public and private bills.
    Private bills should not be discoverable, i.e., refresh_from_db should fail.
    """
    extras = {"restrict_view": restrict_view}

    bill_info = {
        "classification": [bill_type],
        "extras": extras,
    }

    some_bill = bill.build(**bill_info)

    if has_action:
        bill_action.build(bill=some_bill)

    event_related_entity_info = {
        "bill": some_bill,
    }

    related_entity = event_related_entity.build(**event_related_entity_info)

    event = related_entity.agenda_item.event
    event.status = event_status
    event.save()

    event.refresh_from_db()
    related_entity.refresh_from_db()

    try:
        some_bill.refresh_from_db()
    except ObjectDoesNotExist:
        assert is_public is False
    else:
        bill_qs_with_manager = LAMetroBill.objects.filter(id=some_bill.id)
        assert is_public == (some_bill in bill_qs_with_manager)


@pytest.mark.django_db
def test_last_action_date_has_already_occurred(bill, event):
    some_bill = bill.build()

    two_weeks_ago = timezone.now() - timedelta(weeks=2)
    two_weeks_from_now = timezone.now() + timedelta(weeks=2)

    id_fmt = "ocd-event/{}"

    for t in (two_weeks_ago, two_weeks_from_now):
        some_event = event.build(id=id_fmt.format(uuid4()), start_date=t.date())
        item = some_event.agenda.create(order=1)
        item.related_entities.create(bill=some_bill)

    # Assert the bill occurs on both agendas.
    assert Event.objects.filter(agenda__related_entities__bill=some_bill).count() == 2

    last_action_date = some_bill.councilmatic_bill.get_last_action_date()

    # Assert the last action matches the event that has already occurred.
    assert last_action_date == two_weeks_ago.date()


@pytest.mark.parametrize("event_has_related_org", [True, False])
@pytest.mark.django_db
def test_actions_and_agendas(
    bill,
    bill_action,
    event,
    event_agenda_item,
    event_related_entity,
    caplog,
    event_has_related_org,
):
    caplog.set_level(logging.WARNING)

    # create a bill with no actions or agendas and confirm actions and agendas
    # is an empty list
    some_bill = bill.build()

    assert some_bill.actions_and_agendas == []

    # add action w/o event and confirm error is logged
    some_action = bill_action.build(bill=some_bill)

    assert some_bill.actions_and_agendas == []

    (log_record,) = (r for r in caplog.records)

    assert "Could not find event corresponding to action" in log_record.message

    # add event to action and confirm action appears
    action_org = some_action.organization
    action_date = some_action.date
    some_event = event.build(
        name=action_org.name, start_date="{} 12:00".format(action_date)
    )

    EventParticipant.objects.create(
        name=action_org.name,
        organization=action_org,
        entity_type="organization",
        event=some_event,
    )

    aaa = some_bill.actions_and_agendas

    assert len(aaa) == 1

    (expected_action,) = aaa

    assert expected_action["organization"] == action_org
    assert expected_action["event"] == some_event
    assert (
        expected_action["date"]
        == datetime.strptime(some_action.date, "%Y-%m-%d").date()
    )
    assert expected_action["description"] == some_action.description

    # add bill to event agenda and confirm it appears
    if event_has_related_org:
        some_agenda_item = event_agenda_item.build(event=some_event)

    else:
        some_event = event.build(
            name="Public Hearing",
            start_date="{} 12:00".format(action_date),
            id="ocd-event/public-hearing",
        )

        some_participant = EventParticipant.objects.create(event=some_event)
        some_agenda_item = event_agenda_item.build(event=some_event)

    event_related_entity.build(agenda_item=some_agenda_item, bill=some_bill)

    aaa = some_bill.actions_and_agendas

    assert len(aaa) == 2

    expected_agenda = aaa[0]  # agenda should appear first

    if event_has_related_org:
        assert expected_agenda["organization"] == action_org
    else:
        assert expected_agenda["organization"] == some_participant

    assert expected_agenda["event"] == some_event
    assert (
        expected_agenda["date"]
        == datetime.strptime(some_action.date, "%Y-%m-%d").date()
    )
    assert expected_agenda["description"] == "SCHEDULED"


@pytest.mark.django_db
def test_related_bill_respects_privacy(bill):
    primary_bill = bill.build()

    public_related_bill = bill.build(
        id="ocd-bill/{}".format(str(uuid4())), slug="public"
    )
    private_related_bill = bill.build(
        id="ocd-bill/{}".format(str(uuid4())),
        slug="private",
        extras={"restrict_view": True},
    )

    for relation in (public_related_bill, private_related_bill):
        RelatedBill.objects.create(bill=primary_bill, related_bill=relation)

    related_bills = primary_bill.related_bills.values_list(
        "related_bill__councilmatic_bill__slug", flat=True
    )

    assert public_related_bill.slug in related_bills
    assert private_related_bill.slug not in related_bills


def test_private_bill(client, bill):
    private_bill = bill.build(
        id="ocd-bill/{}".format(str(uuid4())), extras={"restrict_view": True}
    )
    url = reverse("lametro:bill_detail", kwargs={"slug": private_bill.slug})
    response = client.get(url)
    assert response.status_code == 404
