from itertools import chain

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from legistar.bills import LegistarAPIBillScraper
from opencivicdata.legislative.models import Bill

from lametro.models import LAMetroSubject
from lametro.smartlogic import SmartLogic


class ClassificationMixin:

    CLASSIFICATION_MAP = {
        label: value for value, label in LAMetroSubject.CLASSIFICATION_CHOICES
    }

    @property
    def smartlogic(self):
        if not hasattr(self, '_smartlogic'):
            self._smartlogic = SmartLogic(settings.SMART_LOGIC_KEY)
        return self._smartlogic

    @property
    def classifications(self):
        if not hasattr(self, '_classifications'):
            self._classifications = {
                **{term: self.CLASSIFICATION_MAP['Board Report Type'] for term in self._get_board_report_types()},
                **{term: self.CLASSIFICATION_MAP['Lines / Ways'] for term in self._get_lines_ways()},
                **{term: self.CLASSIFICATION_MAP['Phases'] for term in self._get_phases()},
            }
        return self._classifications

    def _get_board_report_types(self):
        self.stdout.write('Getting board report types')
        return [t['term']['name'] for t in self.smartlogic.terms('CL=Board Report Type')['terms']]

    def _get_lines_ways(self):
        self.stdout.write('Getting lines and ways')
        terms = []

        for term in self.smartlogic.terms('CL=Transportation Method')['terms']:
            term = term['term']

            try:
                narrower_terms, = [term_dict for term_dict in term['hierarchy']
                                   if term_dict['name'] == 'Narrower Term']
            except ValueError:
                continue
            else:
                nt = []

                for term in narrower_terms['fields']:
                    term = term['field']

                    if 'Concept' in term['classes']:
                        related_concepts = self.smartlogic.terms('DE={}'.format(term['id']))
                        nt += [t['term']['name'] for t in related_concepts['terms']]
                    else:
                        nt.append(term['name'])

                terms += nt

        return terms

    def _get_phases(self):
        self.stdout.write('Getting phases')
        return [t['term']['name'] for t in self.smartlogic.terms('CL=Transportation Phase')['terms']]


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
            LAMetroSubject(name=s) for s in current_topics
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
                                                                  self.CLASSIFICATION_MAP['Subjects'])

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
