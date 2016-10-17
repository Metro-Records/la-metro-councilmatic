from django.conf import settings
from django.shortcuts import render
from django.db import connection
from collections import namedtuple
from councilmatic_core.views import BillDetailView, CouncilMembersView, AboutView, CommitteeDetailView
from councilmatic_core.models import *
from lametro.models import LAMetroBill, LAMetroPost

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
          context = super(BillDetailView, self).get_context_data(**kwargs)
          context['actions'] = self.get_object().actions.all().order_by('-order')
          context['attachments'] = self.get_object().attachments.all().order_by('document__note')

          return context

class LABoardMemberView(CouncilMembersView):
    model = LAMetroPost

    def get_queryset(self):
        return LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)

class LAMetroAboutView(AboutView):
    template_name = 'lametro/about.html'


class LACommitteeDetailView(CommitteeDetailView):

    template_name = 'lametro/committee.html'

    def get_context_data(self, **kwargs):
        context = super(CommitteeDetailView, self).get_context_data(**kwargs)

        committee = context['committee']

        with connection.cursor() as cursor:

            sql = ('''
              SELECT
                p.*,
                mm.role,
                mm.label
              FROM councilmatic_core_membership AS m
              JOIN (
                SELECT
                  person_id,
                  m.role,
                  p.label
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_post AS p
                ON m.post_id=p.id
                WHERE m.organization_id = (
                  SELECT id from councilmatic_core_organization
                  WHERE ocd_id= %s)
              ) AS mm
                USING(person_id)
              JOIN councilmatic_core_organization AS o
                ON m.organization_id = o.id
              JOIN councilmatic_core_person AS p
                ON m.person_id = p.id
              WHERE m.organization_id = %s
            ''')

            cursor.execute(sql, [settings.OCD_CITY_COUNCIL_ID, committee.id])

            # results = cursor.fetchall()

            # print(len(results))

            columns = [c[0] for c in cursor.description]
            print(columns)
            id_tuple = namedtuple('label', columns)
            objs = [id_tuple(*r) for r in cursor]
            print(objs)

            context['objs'] = objs

        # donation_trend = []
        # expend_trend = []

        # amounts = [amount_tuple(*r) for r in cursor]

        committee = context['committee']
        context['memberships'] = committee.memberships.all()

        memberships = context['memberships']

        orgs = Membership.objects.filter(_organization_id=committee.id)

        people = [m.person for m in memberships]

        committee_ocd_id = committee.ocd_id

        # posts = LAMetroPost.objects.filter(_organization__ocd_id=this_id)
        # All posts.
        select_posts = []
        posts = LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)
        for p in posts:
          if p.current_member.person in people:
            select_posts.append(p)

        print(select_posts)

        return context
