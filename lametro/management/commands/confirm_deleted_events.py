import logging
import requests

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent
from django.conf import settings


logger = logging.getLogger(__name__)


def check_deleted(url: str):
    """
    Check API response, return True if response is NOT ok.
    """
    key = settings.LEGISTAR_TOKEN

    if not key:
        raise ValueError(
            "No API key found, please provide one in your "
            "environment variables so no events are "
            "incorrectly marked deleted"
        )

    res = requests.get(url + "?token={}".format(key))
    return not res.ok


class Command(BaseCommand):
    """
    Check Legistar for possibly deleted events, and flag all events that
    are not found, that is, that have actually been deleted.
    """

    def handle(self):

        possible_deletions = LAMetroEvent.possibly_deleted_meetings()

        for d in possible_deletions:
            url = d.api_source
            if url:
                d.extras["deleted_in_legistar"] = check_deleted(url)
                d.save()
