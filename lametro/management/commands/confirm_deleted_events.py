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

    def add_arguments(self, parser):
        parser.add_argument(
            "--max",
            required=False,
            default=10,
            type=int,
            help="Max number of items allowed to be flagged as deleted in Legistar at once (not counting test events).",
        )

    def handle(self, *args, **options):

        key = settings.LEGISTAR_TOKEN

        if not key:
            raise ValueError(
                "No API key found, please provide one in your "
                "environment variables so no events are "
                "incorrectly marked deleted."
            )

        possible_deletions = (
            LAMetroEvent.objects.including_test_and_deleted_events()
            .filter(media__isnull=True)
            .exclude(documents__note__icontains="minutes")
        )

        logger.info(f"{len(possible_deletions)} possibly deleted meetings found.")

        to_mark_deleted = []
        deleted_test_count: int = 0
        skipped_count: int = 0
        max_failsafe: int = options["max"]

        if not legistar_online():
            raise Exception("Legistar API not reachable.")

        for d in possible_deletions:
            url = str(d.api_source)
            web = str(d.web_source)
            if url and "deleted_in_legistar" not in d.extras:
                deleted = check_deleted(url, key)
                if deleted:
                    to_mark_deleted.append(d)
                    logger.info(f"DEL: {d.event} not found. See {web}")

                    if "test" in d.event.lower():
                        deleted_test_count += 1

                d.extras["deleted_in_legistar"] = deleted

            elif d.extras.get("deleted_in_legistar"):
                logger.info(f"SKIP: {d.event} already marked as deleted. See {web}")
                skipped_count += 1

        if (len(to_mark_deleted) - deleted_test_count) > max_failsafe:
            raise Exception(
                f"Failsafe: More than {max_failsafe} events flagged as deleted, "
                "not including {deleted_test_count} test events."
            )
        else:
            LAMetroEvent.objects.bulk_update(to_mark_deleted, ["extras"])

        logger.info(
            f"{len(to_mark_deleted)}/{len(possible_deletions)} events marked as deleted, "
            f"including {deleted_test_count} test events.\n"
            f"{skipped_count} already marked items still in database.",
        )
