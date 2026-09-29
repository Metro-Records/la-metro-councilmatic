import logging
import requests

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent
from django.conf import settings


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Check Legistar for possibly deleted events, and flag all events that
    are not found, that is, that have actually been deleted.
    """

    def handle(self):

        possible_deletions = LAMetroEvent.possibly_deleted_meetings()

        key = settings.LEGISTAR_TOKEN

        if not key:
            raise ValueError(
                "No API key found, please provide one in your "
                "environment variables so no events are "
                "incorrectly marked deleted"
            )

        for d in possible_deletions:
            if d.api_source:
                res = requests.get(d.api_source + "?token={}".format(key))

                d.extras["deleted_in_legistar"] = not res.ok
                d.save()
