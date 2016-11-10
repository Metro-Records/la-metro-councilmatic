from councilmatic_core.haystack_indexes import BillIndex
from haystack import indexes
from councilmatic_core.models import Action
from lametro.models import LAMetroBill

class LAMetroBillIndex(BillIndex, indexes.Indexable):

    def get_model(self):
        return LAMetroBill

    def prepare_controlling_body(self, obj):
        return None

    def prepare_sponsorships(self, obj):
        actions = Action.objects.filter(_bill_id=obj.ocd_id)
        return [action.organization for action in actions]