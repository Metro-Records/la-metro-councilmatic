import logging
import requests

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Check Legistar for possibly deleted events, and flag all events that
    are not found, that is, that have actually been deleted.
    """

    def handle(self):

        possible_deletions = LAMetroEvent.possibly_deleted_meetings()

        for d in possible_deletions:
            if d.api_source:
                response = requests.head(d.api_source)
                d.extras["deleted_in_legistar"] = not response.ok
                d.save()
