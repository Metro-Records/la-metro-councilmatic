import logging
import requests
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q, F
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
        Send notifications for bills and events recently created/updated if the entity:
        - has not yet had a notification sent
        - has been updated more recently than its last notification
        - does not have a successful notification
        """

        now = datetime.now()
        cutoff_date = now - timedelta(weeks=12)  # 3 months ago
        filters = Q(updated_at__gte=cutoff_date) & (
            Q(notification__isnull=True)
            | Q(notification__date_last_sent__lt=F("updated_at"))
            | Q(notification__was_successful=False)
        )
        bills = LAMetroBill.objects.filter(filters)
        events = LAMetroEvent.objects.filter(filters)
        logger.info(f"Checking {len(bills)} bills and {len(events)} events...")

        if not bills and not events:
            logger.info("All documents up to date!")
            return

        # Check for document details, then aggregate as single list of dicts
        bills_details = BillService.build_bills_notification(bills)
        events_details = EventService.build_events_notification(events)
        if not bills_details and not events_details:
            logger.info("No related documents found for selected bills or events")
            return
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
            logger.warning(f"Failed: {response.json()}")

        # Upsert notification objects for each entity
        self.upsert_notifications(bills, "bill", was_successful, now)
        self.upsert_notifications(events, "event", was_successful, now)
        logger.info("Finished processing notification")

    def upsert_notifications(self, entities, entity_type, was_successful, now):
        for entity in entities:
            data_kwargs = {
                # Populate either the 'bill' or 'event' type field with this entity
                entity_type: entity,
                "defaults": {
                    "entity_type": type,
                    "date_last_sent": now,
                    "was_successful": was_successful,
                },
            }
            TranslationNotification.objects.update_or_create(**data_kwargs)
