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
        get_kwarg = {'ocd_id': settings.OCD_CITY_COUNCIL_ID}
        return Organization.objects.get(**get_kwarg).memberships.all()
        #return Post.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context