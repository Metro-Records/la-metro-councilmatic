from councilmatic_core.models import *
from councilmatic_core.views import BillDetailView, CouncilMembersView
from django.conf import settings
from django.shortcuts import render
from lametro.models import LAMetroBill, LAMetroPost

class LABillDetail(BillDetailView):
    template_name = 'lametro/legislation.html'

class LABoardMemberView(CouncilMembersView):
    model = LAMetroPost

    def get_queryset(self):
        return LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)

#    def get_context_data(self, *args, **kwargs):
#        context = super().get_context_data(**kwargs)
#
#        return context

#    def format_label(self, label):
#        '''
#        Put long labels on two lines!
#        '''
