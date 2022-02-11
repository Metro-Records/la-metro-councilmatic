import logging

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Check the current meetings, marking any live meeting as having been
    broadcast.
    '''
    class Meta:
        proxy = True

    def handle(self, *args, **options):
        current_meetings = LAMetroEvent.current_meeting()

        if current_meetings.exists():
            logger.info('Found current meetings: {}'.format(current_meetings))

            live_meeting = current_meetings.filter(extras__has_broadcast=True)

            if live_meeting:
                logger.info('Meeting marked as has broadcast: {}'.format(live_meeting))

        else:
            logger.info('No current meetings found')
