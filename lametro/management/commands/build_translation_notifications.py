import logging
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Q, F, OuterRef, Subquery

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
    Create notifications for the translation suite of any bills
    or events that need their documents OCR'd and translated.
    """

    help = (
        "Create notifications for the translation suite of any bills "
        "or events that need their documents OCR'd and translated."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=12,
            help="Consider a entity, if it was updated within the last N weeks.",
        )

    def handle(self, *args, **options):
        """
        Create notifications for recent bills and events if the entity:
        - does not yet have any notifications
        - has a failed notification as its latest
        - has been updated more recently than its latest notification

        Notifications will not be made for entities that don't
        have documents to notify about.
        """

        now = datetime.now()
        weeks = options["weeks"]
        cutoff_date = now - timedelta(weeks=weeks)
        filters = Q(updated_at__gte=cutoff_date) & (
            Q(latest_notification_pk__isnull=True)
            | Q(
                notifications__pk=F("latest_notification_pk"),
                notifications__status="failed",
            )
            | Q(
                notifications__pk=F("latest_notification_pk"),
                notifications__created_at__lt=F("updated_at"),
            )
        )

        # Annotate to allow us to filter on just each entity's latest notification
        bills = (
            LAMetroBill.objects.annotate(
                latest_notification_pk=Subquery(
                    TranslationNotification.objects.filter(bill_id=OuterRef("pk"))
                    .order_by("-created_at")
                    .values("pk")[:1]
                )
            )
            .filter(filters)
            .distinct()
        )

        events = (
            LAMetroEvent.objects.annotate(
                latest_notification_pk=Subquery(
                    TranslationNotification.objects.filter(event_id=OuterRef("pk"))
                    .order_by("-created_at")
                    .values("pk")[:1]
                )
            )
            .filter(filters)
            .distinct()
        )

        if not bills and not events:
            logger.info("~~ All document notifications up to date! ~~")
            return
        logger.info(f"Checking {len(bills)} bills and {len(events)} events...")

        # Create new notifications
        bill_notifications = self.create_notifications(bills)
        event_notifications = self.create_notifications(events)

        if not bill_notifications and not event_notifications:
            logger.info("No related documents found for selected bills and events")
            return

        logger.info(
            f"Created notifications for {len(bill_notifications or [])} bills "
            f"and {len(event_notifications or [])} events."
        )

        # Clean up previously failed notifications for these entities
        bills_pks = {b.pk for b in bills}
        events_pks = {e.pk for e in events}
        related_failed_notifs = TranslationNotification.objects.filter(
            Q(status="failed") & (Q(bill__in=bills_pks) | Q(event__in=events_pks))
        )
        related_failed_notifs.delete()

        logger.info("~~ Finished building notifications! ~~")

    def create_notifications(self, qs):
        """
        Create a notification object for each entity in the queryset if that entity
        has relevant related documents. If an entity has no documents to report on,
        a notification will not be made.
        """

        # Determine which entity type this queryset is for, and choose the right builder
        if not qs:
            return
        elif qs.model is LAMetroBill:
            entity_type = "bill"
            detail_builder = BillService.build_bill_document_details
        else:
            entity_type = "event"
            detail_builder = EventService.build_event_document_details

        # Create notifications
        notifications_to_create = []
        for current_entity in qs:
            entity_details = detail_builder(current_entity)
            if not entity_details:
                continue

            data_kwargs = {
                "entity_type": entity_type,
                entity_type: current_entity,
                "data": entity_details,
            }
            notifications_to_create.append(TranslationNotification(**data_kwargs))

        notifications = TranslationNotification.objects.bulk_create(
            notifications_to_create
        )

        return notifications
