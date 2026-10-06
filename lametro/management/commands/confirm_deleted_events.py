import logging
import requests

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent
from django.conf import settings


logger = logging.getLogger(__name__)


def check_deleted(url: str, key: str = ""):
    """
    Check API response, return True if response is NOT ok.
    """

    if key:
        url = url + "?token={}".format(key)

    res = requests.get(url)
    return not res.ok


def legistar_online() -> bool:
    """
    Check if Legistar API is online.
    """

    res = requests.get("https://webapi.legistar.com/v1/metro/bodytypes")
    return res.status_code == 200


class Command(BaseCommand):
    """
    Check Legistar for possibly deleted events, and flag all events that
    are not found, that is, that have actually been deleted.
    """

    def handle(self, *args, **options):

        key = settings.LEGISTAR_TOKEN

        if not key:
            raise ValueError(
                "No API key found, please provide one in your "
                "environment variables so no events are "
                "incorrectly marked deleted."
            )

        possible_deletions = LAMetroEvent.possibly_deleted_meetings()

        logger.info(f"{len(possible_deletions)} possibly deleted meetings found.")

        deleted_count = 0
        skipped_count = 0

        if not legistar_online():
            raise Exception("Legistar API not reachable.")

        for d in possible_deletions:
            url = str(d.api_source)
            web = str(d.web_source)
            if url and not d.extras["deleted_in_legistar"]:
                deleted = check_deleted(url, key)
                if deleted:
                    logger.info(f"DEL: {d.event} not found. See {web}")
                    deleted_count += 1
                d.extras["deleted_in_legistar"] = deleted

            LAMetroEvent.objects.bulk_update(possible_deletions, ["extras"])

            if d.extras["deleted_in_legistar"]:
                logger.info(f"SKIP: {d.event} already marked as deleted. See {web}")
                skipped_count += 1

        logger.info(
            f"{deleted_count}/{len(possible_deletions)} events marked as deleted.\n",
            f"{skipped_count} already marked items still in database.",
        )
