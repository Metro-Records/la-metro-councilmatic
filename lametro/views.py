from django.conf import settings
from django.shortcuts import render
from councilmatic_core.views import BillDetailView
from councilmatic_core.models import *
from lametro.models import LAMetroBill

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
          context = super(BillDetailView, self).get_context_data(**kwargs)
          context['actions'] = self.get_object().actions.all().order_by('-order')

          return context

