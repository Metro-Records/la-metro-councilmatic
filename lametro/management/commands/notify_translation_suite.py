import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Q, F

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
        Send notifications for bills and events if the entity:
        - has not yet had a notification sent
        - has been updated more recently than its last notification
        - does not have a successful notification
        """

        filter_by_notification = (
            Q(notification__isnull=True)
            | Q(notification__date_last_sent__lt=F("updated_at"))
            | Q(notification__was_successful=False)
        )
        bills = LAMetroBill.objects.filter(filter_by_notification)
        events = LAMetroEvent.objects.filter(filter_by_notification)

        if not bills and not events:
            logger.info("All documents up to date!")
            return

        # Notify suite and upsert notification objects for each entity
        if bills:
            self.notify(qs=bills, qs_entity_type="bill")
        if events:
            self.notify(qs=events, qs_entity_type="event")

    def notify(self, qs, qs_entity_type):
        """
        Notify suite of documents for each entity in a queryset
        and upsert notifications.
        """

        if qs_entity_type not in ["bill", "event"]:
            logger.warning("qs_entity_type must be either 'bill' or 'event'")
            return

        logger.info(f"Processing {len(qs)} {qs_entity_type}s...")
        if qs_entity_type == "bill":
            response = BillService.send_bills_notification(qs)
        else:
            response = EventService.send_events_notification(qs)

        logger.info(
            f"{qs_entity_type.title()}s notification returned status code: "
            f"{response.status_code}"
        )
        if str(response.status_code).startswith("20"):
            was_successful = True
            logger.info(f"Success: {response.json()}")
        else:
            was_successful = False
            logger.warning(f"Failed: {response.json()}")

        now = datetime.now()
        for entity in qs:
            data_kwargs = {
                # Populate either the 'bill' or 'event' field with this entity
                qs_entity_type: entity,
                "defaults": {
                    "entity_type": qs_entity_type,
                    "date_last_sent": now,
                    "was_successful": was_successful,
                },
            }
            TranslationNotification.objects.update_or_create(**data_kwargs)

        logger.info(f"Finished {qs_entity_type}s notification")
