import re

from haystack import indexes
from councilmatic_core.haystack_indexes import BillIndex

from lametro.models import LAMetroBill, LAMetroSubject
from lametro.utils import format_full_text, parse_subject

class LAMetroBillIndex(BillIndex, indexes.Indexable):
    topics = indexes.MultiValueField(faceted=True)
    attachment_text = indexes.CharField()
    viewable = indexes.BooleanField()

    # Custom Metro facets
    bill_type = indexes.MultiValueField(faceted=True)
    lines_and_ways = indexes.MultiValueField(faceted=True)
    phase = indexes.MultiValueField(faceted=True)
    project = indexes.MultiValueField(faceted=True)
    metro_location = indexes.MultiValueField(faceted=True)
    geo_admin_location = indexes.MultiValueField(faceted=True)
    significant_date = indexes.MultiValueField(faceted=True)
    motion_by = indexes.MultiValueField(faceted=True)
    plan_program_policy = indexes.MultiValueField(faceted=True)

    def get_model(self):
        return LAMetroBill

    def prepare_controlling_body(self, obj):
        return None

    def prepare_sponsorships(self, obj):
        return [action.organization for action in obj.actions.all()]

    def prepare_sort_name(self, obj):
        full_text = obj.extras.get('plain_text')
        results = ''

        if full_text:
            results = format_full_text(full_text)
            if results:
                return parse_subject(results)
        else:
            return obj.bill_type

    def prepare_attachment_text(self, obj):
        return ' '.join(
            d.extras['full_text'] for d in obj.documents.all()
            if d.extras.get('full_text')
        )

    def prepare_legislative_session(self, obj):
        start_year = obj.legislative_session.identifier
        end_year = int(start_year) + 1

        session = '7/1/{start_year} to 6/30/{end_year}'.format(start_year=start_year,
                                                               end_year=end_year)

        return session

    def prepare_topics(self, obj):
        return self._topics_from_classification(obj, 'topics_exact')

    def prepare_bill_type(self, obj):
        return self._topics_from_classification(obj, 'bill_type_exact')

    def prepare_lines_and_ways(self, obj):
        return self._topics_from_classification(obj, 'lines_and_ways_exact')

    def prepare_phase(self, obj):
        return self._topics_from_classification(obj, 'phase_exact')

    def prepare_project(self, obj):
        return self._topics_from_classification(obj, 'project_exact')

    def prepare_metro_location(self, obj):
        return self._topics_from_classification(obj, 'metro_location_exact')

    def prepare_geo_admin_location(self, obj):
        return self._topics_from_classification(obj, 'geo_admin_location_exact')

    def prepare_significant_date(self, obj):
        return self._topics_from_classification(obj, 'significant_date_exact')

    def prepare_motion_by(self, obj):
        return self._topics_from_classification(obj, 'motion_by_exact')

    def prepare_plan_program_policy(self, obj):
        return self._topics_from_classification(obj, 'plan_program_policy_exact')

    def _topics_from_classification(self, obj, classification):
        '''
        Retrieve a list of topics with the given classification.
        '''
        topics = LAMetroSubject.objects.filter(
            name__in=obj.subject,
            classification=classification
        ).values_list('name', flat=True)

        return list(topics)
