from councilmatic_core.haystack_indexes import BillIndex
from haystack import indexes
from lametro.models import LAMetroBill

class LAMetroBillIndex(BillIndex, indexes.Indexable):
    
    def get_model(self):
        return LAMetroBill
    
    def prepare_controlling_body(self, obj):
        return obj.controlling_body
