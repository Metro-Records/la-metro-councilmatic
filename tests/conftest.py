from datetime import datetime
from datetime import timedelta
import pytest
from uuid import uuid4
from random import randrange

from django.core.management import call_command

from opencivicdata.legislative.models import (
    LegislativeSession,
    EventAgendaItem,
    EventRelatedEntity,
    )
from opencivicdata.core.models import Jurisdiction, Division
from opencivicdata.legislative.models import EventDocument, BillAction
from councilmatic_core.models import Bill, Membership
from lametro.models import LAMetroPerson, LAMetroEvent, LAMetroBill, \
    LAMetroOrganization, LAMetroSubject


def get_uid_chunk(uid=None):
    '''
    Create the UID chunk like the one we append to slugs to ensure
    they're unique.
    '''
    if not uid:
        uid = str(uuid4())

    return uid[:13].replace('-', '')

@pytest.fixture
@pytest.mark.django_db
def bill(db, legislative_session):
    class BillFactory():
        def build(self, **kwargs):
            bill_info = {
                'id': 'ocd-bill/2436c8c9-564f-4cdd-a2ce-bcfe082de2c1',
                'title': 'APPROVE the policy for a Measure M Early Project Delivery Strategy',
                'created_at': '2017-06-09 13:06:21.10075-05',
                'updated_at': '2017-06-09 13:06:21.10075-05',
                'identifier': '2017-0686',
                'slug': '2017-0686',
                'classification': ['Report'],
                'legislative_session': legislative_session,
                'extras': {'restrict_view': False},
            }

            bill_info.update(kwargs)

            bill = LAMetroBill.objects.create(**bill_info)

            return bill

    return BillFactory()


@pytest.fixture
@pytest.mark.django_db
def bill_action(db, bill, metro_organization):
    class BillActionFactory():
        def build(self, **kwargs):
            bill_action_info = {
                'organization': metro_organization.build(),
                'description': 'test action',
                'date': '2019-11-09',
                'order': 999,
            }

            bill_action_info.update(kwargs)

            if not bill_action_info.get('bill'):
                bill_action_info['bill'] = bill.build()

            bill_action = BillAction.objects.create(**bill_action_info)

            return bill_action

    return BillActionFactory()

@pytest.fixture
@pytest.mark.django_db
def division(db):
    division_info = {
        'id': 'ocd-division/country:us/state:ca/county:los_angeles',
        'name': 'LA'
        }

    division = Division.objects.create(**division_info)

    return division

@pytest.fixture
@pytest.mark.django_db
def jurisdiction(db, division):
    jurisdiction_info = {
        'id': 'ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority',
        'division_id': 'ocd-division/country:us/state:ca/county:los_angeles'}

    jurisdiction = Jurisdiction.objects.create(**jurisdiction_info)

    return jurisdiction

@pytest.fixture
@pytest.mark.django_db
def legislative_session(db, jurisdiction):
    session_info = {
        'identifier': '2017',
        'jurisdiction_id': 'ocd-jurisdiction/country:us/state:ca/county:los_angeles/transit_authority',
        'name': '2017 Legislative Session',
    }

    session = LegislativeSession.objects.create(**session_info)

    return session

@pytest.fixture
@pytest.mark.django_db
def event(db, jurisdiction):
    class EventFactory():
        def build(self, **kwargs):
            event_info = {
                'id': 'ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d',
                'created_at': '2017-05-27 11:10:46.574-05',
                'updated_at': '2017-05-27 11:10:46.574-05',
                'name': 'System Safety, Security and Operations Committee',
                'start_date': '2017-05-18 12:15',
                'slug': uuid4(),
                'jurisdiction': jurisdiction,
            }

            event_info.update(kwargs)

            event = LAMetroEvent.objects.create(**event_info)

            return event

    return EventFactory()

@pytest.fixture
@pytest.mark.django_db
def event_agenda_item(db, event):
    class EventAgendaItemFactory():
        def build(self, **kwargs):
            event_agenda_item_info = {
                'order': 1,
            }

            if not kwargs.get('event'):
                kwargs['event'] = event.build()

            event_agenda_item_info.update(kwargs)

            event_agenda_item = EventAgendaItem.objects.create(**event_agenda_item_info)

            return event_agenda_item

    return EventAgendaItemFactory()


@pytest.fixture
@pytest.mark.django_db
def event_related_entity(db, event_agenda_item):
    class EventRelatedEntityFactory():
        def build(self, **kwargs):
            event_related_entity_info = {}

            if not kwargs.get('agenda_item'):
                kwargs['agenda_item'] = event_agenda_item.build()

            event_related_entity_info.update(kwargs)

            event_related_entity = EventRelatedEntity.objects.create(**event_related_entity_info)

            return event_related_entity

    return EventRelatedEntityFactory()


@pytest.fixture
@pytest.mark.django_db
def event_document(db):
    class EventDocumentFactory():
        def build(self, **kwargs):
            event_document_info = {
                'event_id': 'ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d',
            }

            event_document_info.update(kwargs)

            event_document = EventDocument.objects.create(**event_document_info)

            event_document.links.create(url='https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081')

            return event_document

    return EventDocumentFactory()

@pytest.fixture
@pytest.mark.django_db
def metro_person(db):
    class LAMetroPersonFactory():
        def build(self, **kwargs):
            uid = str(uuid4())

            person_info = {
                'id': 'ocd-person/' + uid,
                'name': 'Wonder Woman',
                'slug': 'wonder-woman-' + get_uid_chunk(uid),
            }

            person_info.update(kwargs)

            person = LAMetroPerson.objects.create(**person_info)

            return person

    return LAMetroPersonFactory()

@pytest.fixture
@pytest.mark.django_db
def metro_organization(db):
    class LAMetroOrganizationFactory():
        def build(self, **kwargs):
            uid = str(uuid4())

            organization_info = {
                'id': 'ocd-organization/' + uid,
                'name': 'Planning and Programming Committee ' + uid,
                'slug': 'planning-and-programming-committee-' + get_uid_chunk(uid),
            }

            organization_info.update(kwargs)

            organization = LAMetroOrganization.objects.create(**organization_info)

            return organization

    return LAMetroOrganizationFactory()

@pytest.fixture
@pytest.mark.django_db
def membership(db, metro_organization, metro_person):
    class MembershipFactory():
        def build(self, **kwargs):
            related_org = metro_organization.build()
            related_person =metro_person.build()

            membership_info = {
                'id': randrange(10000),
                'organization': related_org,
                'person': related_person,
                'end_date': (datetime.now() + timedelta(days=7)).date().isoformat()
            }

            membership_info.update(kwargs)

            membership = Membership.objects.create(**membership_info)

            return membership

    return MembershipFactory()

@pytest.fixture
@pytest.mark.django_db
def subject(db, bill):
    class SubjectFactory():
        def build(self, **kwargs):

            if 'bill' in kwargs:
                current_bill = kwargs.get('bill')
            else:
                current_bill = bill.build()

            subject_name = 'Metro Gold Line'

            subject_info = {
                'bill': current_bill,
                'subject': subject_name
            }

            subject_info.update(kwargs)

            subject = Subject.objects.create(**subject_info)

            return subject

    return SubjectFactory()

@pytest.fixture
@pytest.mark.django_db
def metro_subject(db, subject):
    class LAMetroSubjectFactory():
        def build(self, **kwargs):

            if 'name' in kwargs:
                current_subject = kwargs.get('name')
            else:
                current_subject = 'Metro Gold Line'

            if 'guid' in kwargs:
                guid = kwargs.get('guid')
            else:
                guid = '0000-0-0000'

            subject_info = {
                'name': current_subject,
                'guid': guid
            }

            subject_info.update(kwargs)

            subject = LAMetroSubject.objects.create(**subject_info)

            return subject

    return LAMetroSubjectFactory()

@pytest.fixture
def concurrent_current_meetings(event):
    '''
    Two meetings scheduled to begin in the next five minutes.
    '''
    board_meeting_info = {
        'id': 'ocd-event/ef33b22d-b166-458f-b254-b81f656ffc09',
        'name': 'Regular Board Meeting',
        'start_date': LAMetroEvent._time_from_now(minutes=3)\
            .replace(second=0, microsecond=0)\
            .isoformat(),
    }
    board_meeting = event.build(**board_meeting_info)

    construction_meeting_info = {
        'id': 'ocd-event/FEC6A621-F5C7-4A88-B2FB-5F6E14FE0E35',
        'name': 'Construction Committee',
        'start_date': LAMetroEvent._time_from_now(minutes=3)\
            .replace(second=0, microsecond=0)\
            .isoformat(),
    }
    construction_meeting = event.build(**construction_meeting_info)

    return board_meeting, construction_meeting
