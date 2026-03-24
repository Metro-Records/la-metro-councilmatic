import logging
import requests
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q, F, OuterRef, Subquery
from django.conf import settings

from lametro.models.legislative import (
    LAMetroEvent,
    LAMetroBill,
    TranslationNotification,
)
from lametro.services.bill_service import BillService
from lametro.services.event_service import EventService


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Notify the translation suite of any board reports or event documents
    that need text extraction/translation.
    """

    help = (
        "Notify the translation suite of any board reports or event documents "
        "that need text extraction/translation."
    )

    def handle(self, *args, **options):
        """
        Send notifications for recent bills and events if the entity:
        - does not yet have any notifications
        - has been updated more recently than its latest notification
        - was not successful during its latest notification
        """

        now = datetime.now()
        cutoff_date = now - timedelta(weeks=12)  # 3 months ago
        filters = Q(updated_at__gte=cutoff_date) & (
            Q(latest_notification_pk__isnull=True)
            | Q(
                notifications__pk=F("latest_notification_pk"),
                notifications__was_successful=False,
            )
            | Q(
                notifications__pk=F("latest_notification_pk"),
                notifications__date_sent__lt=F("updated_at"),
            )
        )

        # Annotate to allow us to filter on just each entity's latest notification
        bills = LAMetroBill.objects.annotate(
            latest_notification_pk=Subquery(
                TranslationNotification.objects.filter(bill_id=OuterRef("pk"))
                .order_by("-date_sent")
                .values("pk")[:1]
            )
        ).filter(filters)

        events = LAMetroEvent.objects.annotate(
            latest_notification_pk=Subquery(
                TranslationNotification.objects.filter(event_id=OuterRef("pk"))
                .order_by("-date_sent")
                .values("pk")[:1]
            )
        ).filter(filters)

        logger.info(f"Checking {len(bills)} bills and {len(events)} events...")

        if not bills and not events:
            logger.info("All documents up to date!")
            return

        # Get document detail dicts, exclude empty results, and collate into one list
        bills_details = self.get_details(bills)
        events_details = self.get_details(events)

        if not bills_details and not events_details:
            logger.info("No related documents found for selected bills or events")
            return
        logger.info(
            f"Found {len(bills_details)} board reports "
            f"and {len(events_details)} agendas"
        )

        document_details = bills_details + events_details

        # Notify suite
        logger.info(f"Notifying about {len(document_details)} total documents...")
        url = f"https://{settings.TRANSLATION_SUITE_URL}/api/update-documents/"
        data = {"api_key": settings.TRANSLATION_API_KEY, "documents": document_details}

        response = requests.post(
            url, json=data, headers={"Content-type": "application/json"}
        )
        logger.info(f"Translation suite returned status code: {response.status_code}")

        if was_successful := str(response.status_code).startswith("20"):
            logger.info(f"Success: {response.json()}")
        else:
            try:
                logger.warning(f"Failed: {response.json()}")
            except requests.exceptions.JSONDecodeError:
                logger.warning(f"Failed: {response.reason}")

        # Create new notifications for each entity
        self.create_notifications(bills, was_successful, now)
        self.create_notifications(events, was_successful, now)
        logger.info("Finished processing notifications")

    def get_details(self, qs):
        """
        Create a list of dicts containing document details for each entity
        in the queryset, while filtering out any empty results.
        """
        if not qs:
            return []

        if type(qs[0]) == LAMetroBill:
            details = [BillService.build_bill_notification(bill) for bill in qs]
        else:
            details = [EventService.build_event_notification(event) for event in qs]

        return [d for d in details if d]

    def create_notifications(self, qs, was_successful, now):
        """
        Create a notification object for each entity in the queryset.
        The type of the first entity in the queryset will be used to
        determine whether this round of notifications will be for bills or events.
        """
        if not qs:
            return

        entity_type = "bill" if type(qs[0]) == LAMetroBill else "event"
        for entity in qs:
            data_kwargs = {
                "entity_type": entity_type,
                entity_type: entity,
                "date_sent": now,
                "was_successful": was_successful,
            }
            TranslationNotification.objects.create(**data_kwargs)
