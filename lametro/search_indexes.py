from councilmatic_core.haystack_indexes import BillIndex
from haystack import indexes
from councilmatic_core.models import Action
from lametro.models import LAMetroBill
import re

class LAMetroBillIndex(BillIndex, indexes.Indexable):

    def get_model(self):
        return LAMetroBill

    def prepare_controlling_body(self, obj):
        return None

    def prepare_sponsorships(self, obj):
        actions = Action.objects.filter(_bill_id=obj.ocd_id)
        return [action.organization for action in actions]

    def prepare_last_action_date(self, obj):
        actions = Action.objects.filter(_bill_id=obj.ocd_id)

        try:
          action = actions.reverse()[0].date
        except:
          action = ''

        return action

    def prepare_sort_name(self, obj):
        full_text = obj.ocr_full_text
        results = ''

        # Parse the subject line from ocr_full_text
        if full_text:
            txt_as_array = full_text.split("..")
            for item in txt_as_array:
                if 'SUBJECT:' in item:
                    array_with_subject = item.split('\n\n')
                    
                    for el in array_with_subject:
                        if 'SUBJECT:' in el:
                            results = item.replace('\n', '')

        # Isolate text after 'SUBJECT'
        if results:
            before_keyword, keyword, after_keyword = results.partition('SUBJECT:')
            if after_keyword:
                # Do not corrupt search results with brackets
                if '[PROJECT OR SERVICE NAME]' not in after_keyword and '[DESCRIPTION]' not in after_keyword and '[CONTRACT NUMBER]' not in after_keyword:
                    return after_keyword.strip()

        return obj.bill_type
