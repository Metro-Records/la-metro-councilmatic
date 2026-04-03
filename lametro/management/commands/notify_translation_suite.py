import logging
import requests
from time import sleep

from django.core.management.base import BaseCommand
from django.db.models import Q
from django.conf import settings

from lametro.models.legislative import TranslationNotification


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Send all waiting notifications to the translation suite with information
    on each document that needs extraction/translation,
    then clean up failed notifications.
    """

    help = (
        "Send all waiting notifications to the translation suite with information "
        "on each document that needs extraction/translation, "
        "then clean up failed notifications."
    )

    def handle(self, *args, **options):
        """
        Send all waiting notifications and update their statuses.

        On success, mark as delivered and delete all previously failed notifications
        for related entities.

        On failure, retry a set number of times, ultimately marking them as "failed"
        if we exceed our retry limit. The `build_translation_notifications` command
        will make new "waiting" notifications for these entities next time it runs.
        """

        notifications = TranslationNotification.objects.select_related(
            "bill", "event"
        ).filter(status="waiting")

        if not notifications:
            logger.info("~~ No notifications are waiting to be delivered ~~")
            return

        # Notify suite
        logger.info(f"Sending {len(notifications)} notifications...")
        document_details = [n.data for n in notifications]
        url = f"https://{settings.TRANSLATION_SUITE_URL}/api/update-documents/"
        data = {"api_key": settings.TRANSLATION_API_KEY, "documents": document_details}

        was_successful = False
        attempt_limit = 3
        attempt_num = 0
        delay_seconds = 30
        while attempt_num < attempt_limit:
            response = requests.post(
                url, json=data, headers={"Content-type": "application/json"}
            )
            logger.info(
                f"Translation suite returned status code: {response.status_code}"
            )

            # Stop the loop if successful
            if was_successful := str(response.status_code).startswith("20"):
                logger.info(f"Success: {response.json()}")
                break

            # Wait and try again, if under our attempt limit
            attempt_num += 1
            try:
                logger.warning(f"Failed: {response.json()}")
            except requests.exceptions.JSONDecodeError:
                logger.warning(f"Failed: {response.reason}")

            if attempt_num < attempt_limit:
                delay_seconds *= attempt_num
                logger.warning(f"Trying again in {delay_seconds} seconds...")
                sleep(delay_seconds * attempt_num)

        # Update notifications
        if was_successful:
            related_bill_pks = set()
            related_event_pks = set()
            for notif in notifications:
                notif.status = "delivered"

                entity = notif.bill if notif.bill else notif.event
                (
                    related_bill_pks.add(entity.pk)
                    if notif.bill
                    else related_event_pks.add(entity.pk)
                )

            TranslationNotification.objects.bulk_update(notifications, ["status"])

            # Clean up failed notifications for related entities
            failed_filters = Q(status="failed") & (
                Q(bill__pk__in=related_bill_pks) | Q(event__pk__in=related_event_pks)
            )
            TranslationNotification.objects.filter(failed_filters).delete()
            logger.info("~~ Notifications delivered and updated! ~~")
        else:
            for notif in notifications:
                notif.status = "failed"
            TranslationNotification.objects.bulk_update(notifications, ["status"])
            logger.warning(f"~~ Notifications failed after {attempt_limit} attempts ~~")
