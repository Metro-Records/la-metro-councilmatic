from councilmatic_core.models import *
from councilmatic_core.views import BillDetailView
from django.conf import settings
from django.shortcuts import render

class LABillDetail(BillDetailView):
  template_name = 'lametro/legislation.html'