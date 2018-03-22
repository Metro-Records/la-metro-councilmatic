import datetime
import pytest
from uuid import uuid4

from django.core.management import call_command

from councilmatic_core.models import Event, EventDocument, Bill
from lametro.models import LAMetroPerson


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
def bill(db):
    class BillFactory():
        def build(self, **kwargs):
            bill_info = {
                'ocd_id': 'ocd-bill/2436c8c9-564f-4cdd-a2ce-bcfe082de2c1',
                'description': 'APPROVE the policy for a Measure M Early Project Delivery Strategy',
                'ocd_created_at': '2017-06-09 13:06:21.10075-05',
                'ocd_updated_at': '2017-06-09 13:06:21.10075-05',
                'updated_at': '2017-07-26 11:06:47.1853',
                'identifier': '2017-0686',
                'slug': '2017-0686'
            }

            bill_info.update(kwargs)

            bill = Bill.objects.create(**bill_info)
            bill.save()

            return bill

    return BillFactory()

@pytest.fixture
@pytest.mark.django_db
def event(db):
    class EventFactory():
        def build(self, **kwargs):
            event_info = {
                'ocd_id': 'ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d',
                'ocd_created_at': '2017-05-27 11:10:46.574-05',
                'ocd_updated_at': '2017-05-27 11:10:46.574-05',
                'name': 'System Safety, Security and Operations Committee',
                'start_time': '2017-05-18 12:15:00-05',
                'updated_at': '2017-05-17 11:06:47.1853'
            }

            event_info.update(kwargs)

            event = Event.objects.create(**event_info)
            event.save()

            return event

    return EventFactory()

@pytest.fixture
@pytest.mark.django_db
def event_document(db):
    class EventDocumentFactory():
        def build(self, **kwargs):
            event_document_info = {
                'url': 'https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081',
                'event_id': 'ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d',
                'updated_at': '2017-05-16 11:06:47.1853'
            }

            event_document_info.update(kwargs)

            event_document = EventDocument.objects.create(**event_document_info)
            event_document.save()

            return event_document

    return EventDocumentFactory()

@pytest.fixture
@pytest.mark.django_db
def metro_person(db):
    class LAMetroPersonFactory():
        def build(self, **kwargs):
            uid = str(uuid4())

            person_info = {
                'ocd_id': 'ocd-person/' + uid,
                'name': 'Wonder Woman',
                'slug': 'wonder-woman-' + get_uid_chunk(uid),
            }

            person_info.update(kwargs)

            person = LAMetroPerson.objects.create(**person_info)

            return person

    return LAMetroPersonFactory()
