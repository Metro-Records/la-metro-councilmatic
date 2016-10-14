import re

from django.conf import settings
from django.shortcuts import render
from councilmatic_core.views import BillDetailView, CouncilMembersView, PersonDetailView
from councilmatic_core.models import *
from lametro.models import LAMetroBill, LAMetroPost, LAMetroPerson

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
          context = super(BillDetailView, self).get_context_data(**kwargs)
          context['actions'] = self.get_object().actions.all().order_by('-order')

          return context

class LABoardMembersView(CouncilMembersView):
    model = LAMetroPost

    def get_queryset(self):
        return LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)

class LAPersonDetailView(PersonDetailView):
    '''

    '''
    model = LAMetroPerson

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        person = context['person']

        title = ''
        if person.current_council_seat:
            m = person.latest_council_membership.post
            title = '%s as %s' % (m.role, m.label)
        else:
            title = 'Former %s' % person.latest_council_membership.post.role
        context['title'] = title

        return context


