from collections import ChainMap
from itertools import chain

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from legistar.bills import LegistarAPIBillScraper
from opencivicdata.legislative.models import Bill

from lametro.models import LAMetroSubject
from lametro.smartlogic import SmartLogic


class ClassificationMixin:
    '''
    TODO: Add geographic/administrative location facet
    '''
    DEFAULT_FACET = 'topics_exact'

    FACET_CLASSES = {
        'bill_type_exact': (
            'Board Report Type',
        ),
        'lines_and_ways_exact': (
            'Transportation Method',
            'Bus Line',
            'Bus Way',
            'Rail Line',
        ),
        'phase_exact': (
            'Transportation Phase',
        ),
        'project_exact': (
            'Project',
            'Project Development',
            'Project Finance',
            'Capital Project',
            'Construction Project',
            'Grant Project',
            'Other Working Project',
        ),
        'location_exact': (
            'All Transportation Locations',
            'Alignment',
            'Division',
            'Employee Parking Lot',
            'Pank ‘n’ Ride',
            'Radio Station',
            'Route',
            'Station',
            'Surplus, Temporary And Miscellaneous Property',
            'Terminal',
            'Transportation Location',
        ),
        'significant_date_exact': (
            'Dates',
        ),
        'motion_by_exact': (
            'Board Member',
        ),
    }

    @property
    def smartlogic(self):
        if not hasattr(self, '_smartlogic'):
            self._smartlogic = SmartLogic(settings.SMART_LOGIC_KEY)
        return self._smartlogic

    @property
    def classifications(self):
        if not hasattr(self, '_classifications'):
            self._classifications = ChainMap(*[
                {subject: facet for subject in list(self.get_subjects_from_classes(facet, classes))}
                for facet, classes in self.FACET_CLASSES.items()
            ])

        return self._classifications

    def get_subjects_from_classes(self, facet_name, classes):
        self.stdout.write('Getting {}'.format(facet_name))

        for cls in classes:
            response = self.smartlogic.terms('CL={}'.format(cls))
            yield from (t['term']['name'] for t in response['terms'])


class Command(BaseCommand, ClassificationMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.legistar = LegistarAPIBillScraper()
        self.legistar.BASE_URL = 'https://webapi.legistar.com/v1/metro'
        self.legistar.retry_attempts = 0
        self.legistar.requests_per_minute = 0

    def handle(self, *args, **options):
        current_topics = set(chain(*Bill.objects.values_list('subject', flat=True)))

        # Delete topics no longer associated with any bills.
        deleted, _ = LAMetroSubject.objects.exclude(name__in=current_topics).delete()

        self.stdout.write('Removed {0} stale topics'.format(deleted))

        # Create LAMetroSubject instances for all existing topics. Subjects are
        # unique on name. Ignore conflicts so we can bulk create instances
        # without querying for or introducing duplicates.
        LAMetroSubject.objects.bulk_create([
            LAMetroSubject(name=s, classification=self.DEFAULT_FACET) for s in current_topics
        ], ignore_conflicts=True)

        for_update = []

        for topic in self.legistar.topics():
            try:
                subject = LAMetroSubject.objects.get(name=topic['IndexName'])
            except LAMetroSubject.DoesNotExist:
                # The database only contains topics that are related to at least
                # one bill. By contrast, the API contains all topics, regardless
                # of whether they're currently in use. Skip unused topics.
                pass
            else:
                self.stdout.write('Updating {}'.format(subject))

                subject.guid = topic['api_metadata']
                subject.classification = self.classifications.get(subject.name,
                                                                  self.DEFAULT_FACET)

                self.stdout.write('Classification: {}'.format(subject.classification))

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
