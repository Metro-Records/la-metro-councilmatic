from itertools import chain

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from legistar.bills import LegistarAPIBillScraper
from lametro.models import LAMetroSubject
from opencivicdata.legislative.models import Bill


class Command(BaseCommand):
    def _get_board_report_types(self):
        '''
        TODO: Generate this list dynamically.

        TODO: Refactor this command to handle several different classifications
        sourced from assorted SES queries.
        '''
        return (
            'Annual reports',
            'Informational Report',
            'Police reports',
            'Technical reports',
            'Board Correspondence',
            'Oral Report / Presentation',
            'Project Status Report',
            'Environmental Impact Report',
        )

    def handle(self, *args, **options):

        scraper = LegistarAPIBillScraper()
        scraper.BASE_URL = 'https://webapi.legistar.com/v1/metro'
        scraper.retry_attempts = 0
        scraper.requests_per_minute = 0

        current_topics = set(chain(*Bill.objects.values_list('subject', flat=True)))

        # Create LAMetroSubject instances for all existing topics. Subjects are
        # unique on name. Ignore conflicts so we can bulk create instances
        # without querying for or introducing duplicates.
        LAMetroSubject.objects.bulk_create([
            LAMetroSubject(name=s) for s in current_topics
        ], ignore_conflicts=True)

        # Delete topics no longer associated with any bills.
        deleted, _ = LAMetroSubject.objects.exclude(name__in=current_topics).delete()

        self.stdout.write('Removed {0} stale topics'.format(deleted))

        board_report_types = self._get_board_report_types()

        for_update = []

        for topic in scraper.topics():
            try:
                subject = LAMetroSubject.objects.get(name=topic['IndexName'])
            except LAMetroSubject.DoesNotExist:
                self.stdout.write('Could not find LAMetroSubject with name {}'.format(topic['IndexName']))
            else:
                subject.guid = topic['api_metadata']

                # TODO: Refactor this to support multiple kinds of report type.
                if subject.name in board_report_types:
                    subject.classification.append('Board Report Type')
                else:
                    subject.classification = list(filter(lambda x: x != 'Board Report Type', subject.classification))

                for_update.append(subject)

        LAMetroSubject.objects.bulk_update(for_update, ['guid', 'classification'])

        update_count = len(for_update)
        topic_count = LAMetroSubject.objects.count()

        try:
            assert update_count == topic_count
        except AssertionError:
            raise AssertionError('Updated only {0} of {1} total topics'.format(update_count, topic_count))
        else:
            self.stdout.write('Updated all {0} topics'.format(topic_count))
