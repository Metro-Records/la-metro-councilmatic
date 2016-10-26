import re
from datetime import datetime
from itertools import groupby

from django.conf import settings
from django.shortcuts import render
from django.db import connection
from django.db.models.functions import Lower
from django.utils import timezone
from collections import namedtuple
from councilmatic_core.views import IndexView, BillDetailView, CouncilMembersView, AboutView, CommitteeDetailView, CommitteesView, PersonDetailView, EventDetailView
from councilmatic_core.models import *
from lametro.models import LAMetroBill, LAMetroPost, LAMetroPerson

class LAMetroIndexView(IndexView):
    template_name = 'lametro/index.html'

class LABillDetail(BillDetailView):
    model = LAMetroBill
    template_name = 'lametro/legislation.html'

    def get_context_data(self, **kwargs):
          context = super(BillDetailView, self).get_context_data(**kwargs)
          context['actions'] = self.get_object().actions.all().order_by('-order')
          context['attachments'] = self.get_object().attachments.all().order_by(Lower('note'))
          item = context['legislation']
          context['sponsorships'] = item.sponsorships.all().distinct('_person')

          return context

class LABoardMembersView(CouncilMembersView):
    model = LAMetroPost

    def get_queryset(self):
        return LAMetroPost.objects.filter(_organization__ocd_id=settings.OCD_CITY_COUNCIL_ID)

class LAMetroAboutView(AboutView):
    template_name = 'lametro/about.html'

class LACommitteesView(CommitteesView):
    template_name = 'lametro/committees.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Want to remove AD-HOC?
        # WHERE m.end_date::date > NOW()::date
        with connection.cursor() as cursor:

            sql = ('''
              SELECT DISTINCT on (o.ocd_id, m.person_id) o.*, m.person_id, m.role, p.name
              FROM councilmatic_core_organization AS o
              JOIN councilmatic_core_membership AS m
              ON o.ocd_id=m.organization_id
              JOIN councilmatic_core_person as p
              ON p.ocd_id=m.person_id
              WHERE o.classification='committee'
              AND m.end_date::date > NOW()::date
              ORDER BY o.ocd_id, m.person_id, m.end_date;
                ''')

            cursor.execute(sql)

            columns           = [c[0] for c in cursor.description]
            committees_tuple  = namedtuple('Committee', columns, rename=True)
            data              = [committees_tuple(*r) for r in cursor]
            groups            = []

            for key, group in groupby(data, lambda x: x[1]):
                groups.append(list(group))

            committees_list = groups
            context["committees_list"] = committees_list

        return context

class LACommitteeDetailView(CommitteeDetailView):

    template_name = 'lametro/committee.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        committee = context['committee']

        with connection.cursor() as cursor:

            sql = ('''
              SELECT
                p.*,
                m.role,
                mm.label
              FROM councilmatic_core_membership AS m
              LEFT JOIN (
                SELECT
                  person_id,
                  m.role,
                  pt.label
                FROM councilmatic_core_membership AS m
                JOIN councilmatic_core_post AS pt
                  ON m.post_id=pt.ocd_id
                WHERE m.organization_id = %s
              ) AS mm
                USING(person_id)
              JOIN councilmatic_core_person AS p
                ON m.person_id = p.ocd_id
              WHERE m.organization_id = %s
              AND m.end_date::date > NOW()::date
              ORDER BY
                CASE
                  WHEN m.role='Chair' THEN 1
                  WHEN m.role='Vice Chair' THEN 2
                  WHEN m.role='Member' THEN 3
                  ELSE 4
                END
            ''')

            cursor.execute(sql, [settings.OCD_CITY_COUNCIL_ID, committee.ocd_id])

            columns = [c[0] for c in cursor.description]

            results_tuple = namedtuple('Result', columns)

            objects_list = [results_tuple(*r) for r in cursor]

            context['objects_list'] = objects_list

        return context

class LAPersonDetailView(PersonDetailView):

    template_name = 'lametro/person.html'
    model = LAMetroPerson

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        person = context['person']

        title = ''
        qualifying_post = '' # board membership criteria met by person in question
        m = person.latest_council_membership
        if person.current_council_seat:
            title = m.role
            if m.post:
                qualifying_post = m.post.label
        else:
            title = 'Former %s' % m.role
        context['title'] = title
        context['qualifying_post'] = qualifying_post

        if person.committee_sponsorships:
            context['sponsored_legislation'] = [
                s.bill for s in sorted(person.committee_sponsorships, key=lambda obj: obj.date, reverse=True)[:10]
            ]
        else:
            context['sponsored_legislation'] = []

        # TO-DO
        # resolve last_action_date conflict -- should i code in here,
        # override the template, or change the method in django-councilmatic
        # to be consistent w other attribute names? (currently overriden in
        # template, but last_action is referenced in several other places
        # in django-councilmatic)

        return context
