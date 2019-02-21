import re

from haystack import indexes
from councilmatic_core.haystack_indexes import BillIndex
from councilmatic_core.models import Action, EventAgendaItem

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
        actions = Action.objects.filter(_bill_id=obj.ocd_id)
        return [action.organization for action in actions]

    def prepare_last_action_date(self, obj):
        # Solr seems to be fussy about the time format, and we do not need the time, just the date stamp.
        # https://lucene.apache.org/solr/guide/7_5/working-with-dates.html#date-formatting
        last_action_date = obj.get_last_action_date()
        if last_action_date:
            return last_action_date.date()

    def prepare_sort_name(self, obj):
        full_text = obj.ocr_full_text
        results = ''

        if full_text:
            results = format_full_text(full_text)
            if results:
                return parse_subject(results)
        else:
            return obj.bill_type

    def prepare_topics(self, obj):
        return [s.subject for s in obj.subjects.all()]

    def prepare_attachment_text(self, obj):
        return ' '.join(d.full_text for d in obj.documents.all() if d.full_text)

    def prepare_viewable(self, obj):
        return obj.is_viewable
