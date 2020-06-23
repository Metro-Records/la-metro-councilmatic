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
                **{term: self.CLASSIFICATION_MAP['Board Report Type'] for term in self.get_board_report_types()},
                **{term: self.CLASSIFICATION_MAP['Lines / Ways'] for term in self.get_lines_ways()},
                **{term: self.CLASSIFICATION_MAP['Phase'] for term in self.get_phases()},
                **{term: self.CLASSIFICATION_MAP['Project'] for term in self.get_projects()},
                **{term: self.CLASSIFICATION_MAP['Location'] for term in self.get_locations()},
                **{term: self.CLASSIFICATION_MAP['Significant Date'] for term in self.get_significant_dates()},
                **{term.replace(u'\u200b', ''): self.CLASSIFICATION_MAP['Motion By'] for term in self.get_motion_by()},
            }

        return self._classifications

    def _get_flat_terms(self, term_json):
        return [t['term']['name'] for t in term_json]

    def _get_nested_terms(self, term_json):
        terms = []

        for term in term_json:
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

    def get_board_report_types(self):
        self.stdout.write('Getting board report types')
        terms = self.smartlogic.terms('CL=Board Report Type')['terms']
        return self._get_flat_terms(terms)

    def get_lines_ways(self):
        self.stdout.write('Getting lines and ways')
        terms = self.smartlogic.terms('CL=Transportation Method')['terms']
        return self._get_nested_terms(terms)

    def get_phases(self):
        self.stdout.write('Getting phases')
        terms = self.smartlogic.terms('CL=Transportation Phase')['terms']
        return self._get_flat_terms(terms)

    def get_projects(self):
        self.stdout.write('Getting projects')
        terms = self.smartlogic.terms('CL=Project')['terms']
        return self._get_flat_terms(terms)

    def get_locations(self):
        self.stdout.write('Getting locations')
        terms = self.smartlogic.terms('CL=All Locations')['terms']
        return self._get_flat_terms(terms)

    def get_significant_dates(self):
        self.stdout.write('Getting significant dates')
        terms = self.smartlogic.terms('CL=Significant Dates')['terms']
        return self._get_flat_terms(terms)

    def get_motion_by(self):
        self.stdout.write('Getting motion by')
        terms = self.smartlogic.terms('CL=Board Member')['terms']
        return self._get_flat_terms(terms)


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
            LAMetroSubject(name=s, classification=self.CLASSIFICATION_MAP['Subject']) for s in current_topics
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
                                                                  self.CLASSIFICATION_MAP['Subject'])

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
