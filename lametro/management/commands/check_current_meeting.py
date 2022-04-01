import logging

from django.core.management.base import BaseCommand

from lametro.models import LAMetroEvent, EventBroadcast


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    '''
    Create record of meeting stream, if one exists.
    '''
    def handle(self, *args, **options):
        streaming_meeting = LAMetroEvent._streaming_meeting()

        if streaming_meeting.exists():
            streaming_meeting = streaming_meeting.get()

            EventBroadcast.objects.create(event=streaming_meeting)

            logger.info('Meeting marked as has broadcast: {}'.format(streaming_meeting))

        else:
            logger.info('No streaming meetings found')
