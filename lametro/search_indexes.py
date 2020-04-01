import re

from haystack import indexes
from councilmatic_core.haystack_indexes import BillIndex

from lametro.models import LAMetroBill
from lametro.utils import format_full_text, parse_subject

class LAMetroBillIndex(BillIndex, indexes.Indexable):
    topics = indexes.MultiValueField(faceted=True)
    attachment_text = indexes.CharField()
    viewable = indexes.BooleanField()

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

    def prepare_topics(self, obj):
        return obj.topics

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
