from typing import Optional
import logging

import requests

from django.db.models.functions import Cast
from django.db.models import Prefetch, Case, When, IntegerField, QuerySet
from django.urls import reverse
from wagtail.admin.admin_url_finder import AdminURLFinder

from opencivicdata.legislative.models import BillVersion, EventDocument

from lametro.models import LAMetroBill, EventAgenda, EventNotice
from lametro.utils import timed_get, LAMetroRequestTimeoutException

logger = logging.getLogger(__name__)

TOKEN: Optional[str] = None

try:
    from lametro.secrets import TOKEN
except ImportError:
    logger.warning(
        "No API token provided. Future events may be allowed to be deleted in the UI."
    )


class EventService:
    @staticmethod
    def assert_consistent_with_api(event) -> bool:
        if not event.api_source:
            return False

        api_url = event.api_source.url + f"?token={TOKEN}" if TOKEN else ""

        try:
            response: requests.Response = timed_get(api_url, timeout=3)
            response.raise_for_status()

        except (
            LAMetroRequestTimeoutException,
            requests.Timeout,
            requests.ConnectionError,
        ):
            logger.warning(f"Request to {api_url} timed out.")
            return False

        except requests.HTTPError:
            logger.warning(
                f"Request to {api_url} resulted in non-200 status code: {response.status_code}"
            )
            return False

        api_rep: dict = response.json()

        api_body_name: str = ""

        if event.name == "Regular Board Meeting":
            api_body_name = "Board of Directors - Regular Board Meeting"
        elif event.name == "Special Board Meeting":
            api_body_name = "Board of Directors - Special Board Meeting"
        else:
            api_body_name = event.name

        return api_rep["EventBodyName"] == api_body_name

    @staticmethod
    def get_minutes(event) -> Optional[EventDocument]:
        try:
            return event.documents.filter(note__icontains="minutes")
        except EventDocument.DoesNotExist:
            return None

    @staticmethod
    def get_related_board_reports(event) -> QuerySet:
        related_bills = (
            LAMetroBill.objects.with_latest_actions()
            .defer("extras")
            .filter(eventrelatedentity__agenda_item__event=event)
            .prefetch_related(
                Prefetch(
                    "versions",
                    queryset=BillVersion.objects.filter(
                        note="Board Report"
                    ).prefetch_related("links"),
                    to_attr="br",
                ),
                "packet",
            )
        )

        return (
            event.agenda.filter(related_entities__bill__versions__isnull=False)
            .annotate(int_order=Cast("order", IntegerField()))
            .order_by("int_order")
            .prefetch_related(
                Prefetch("related_entities__bill", queryset=related_bills)
            )
        )

    @staticmethod
    def get_agenda(event) -> Optional[dict]:
        documents = (
            event.documents.annotate(
                precedence=Case(
                    When(note__icontains="manual", then=2),
                    When(note__icontains="agenda", then=1),
                    default=999,
                    output_field=IntegerField(),
                )
            )
            .order_by("precedence")
            .prefetch_related("links")
        )

        if documents:
            agenda = documents.first()
            return {
                "url": agenda.links.get().url,
                "timestamp": agenda.date,
                "manual": "manual" in agenda.note.lower(),
            }

        return None

    @staticmethod
    def get_manage_agenda_url(event) -> str:
        manage_agenda_url: str = ""

        try:
            manual_agenda = EventAgenda.objects.get(event=event)
        except EventAgenda.DoesNotExist:
            manage_agenda_url = f"{reverse(EventAgenda.snippet_viewset.get_url_name('add'))}?event={event.slug}"
        else:
            finder = AdminURLFinder()
            manage_agenda_url = finder.get_edit_url(manual_agenda)

        return manage_agenda_url

    @staticmethod
    def get_notices(event) -> QuerySet:
        if event.accepts_live_comment:
            notices_by_comment = EventNotice.objects.filter(
                comment_conditions__contains=["accepts_live_comment"]
            )
        elif event.accepts_public_comment:
            notices_by_comment = EventNotice.objects.filter(
                comment_conditions__contains=["accepts_comment"]
            )
        else:  # Events that do not accept public comment at all
            notices_by_comment = EventNotice.objects.filter(
                comment_conditions__contains=["accepts_no_comment"]
            )

        # Further filter notices by event broadcast status
        for status in ("upcoming", "ongoing", "concluded"):
            status_attr = f"is_{status}" if status != "concluded" else "has_passed"
            if getattr(event, status_attr):
                return notices_by_comment.filter(
                    broadcast_conditions__contains=[status]
                )

        return notices_by_comment.filter(broadcast_conditions__contains=["future"])
