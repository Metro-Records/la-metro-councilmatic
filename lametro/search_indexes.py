import json
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

    # Preloaded fields for display
    listing_description = indexes.CharField(indexed=False)
    last_action_description = indexes.CharField(indexed=False)
    primary_sponsor = indexes.CharField(indexed=False)
    rich_topics = indexes.CharField(indexed=False)
    pseudo_topics = indexes.CharField(indexed=False)

    def get_model(self):
        return LAMetroBill

    def prepare_controlling_body(self, obj):
        return None

    def prepare_sponsorships(self, obj):
        orgs_list = [action['organization'].name for action in obj.actions_and_agendas]
        return set(orgs_list)

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
        aa = sorted(obj.actions_and_agendas, key=lambda i: i['date'],reverse=True)
        agendas = [a for a in aa if a['description'] == 'SCHEDULED']
        if len(aa) > 1:
            if agendas:
                action_date = agendas[0]['date']
            else:
                action_date = aa[0]['date']

            if action_date.month <= 6:
                start_year = action_date.year - 1
                end_year = action_date.year
            else:
                start_year = action_date.year
                end_year = action_date.year + 1

            session = '7/1/{start_year} to 6/30/{end_year}'.format(start_year=start_year,
                                                                   end_year=end_year)
            return session
        return None


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

    def prepare_listing_description(self, obj):
        return obj.listing_description

    def prepare_last_action_description(self, obj):
        if obj.current_action:
            return obj.current_action.description

    def prepare_primary_sponsor(self, obj):
        if obj.primary_sponsor:
            return obj.primary_sponsor.name

    def prepare_rich_topics(self, obj):
        return json.dumps(
            list(obj.rich_topics.values('name', 'classification'))
        )

    def prepare_pseudo_topics(self, obj):
        return json.dumps(
            list({'name': o.name} for o in obj.pseudo_topics)
        )
