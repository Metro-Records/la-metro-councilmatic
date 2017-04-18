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
        # return obj.friendly_name.replace(" ", "")
        text = ''

        full_text = obj.ocr_full_text

        if full_text:
            txt_as_array = full_text.split("..")

            for arr in txt_as_array:
                if arr:
                    sliced_arr = arr.split( )[1:]
                    text += " ".join(sliced_arr) + "<br /><br />"

        text_snippet = None

        if text:
            text_slice = text[:200]
            re_results = re.search(r'SUBJECT:(.*?)ACTION:', str(text))
            if re_results:
                text_snippet = re_results.group(1).lstrip()

        return text_snippet
