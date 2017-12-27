import pytest

from django.core.urlresolvers import reverse

from councilmatic_core.models import Event, EventDocument, Bill, RelatedBill
from lametro.models import LAMetroEvent
from lametro.templatetags.lametro_extras import updates_made
from lametro.forms import AgendaPdfForm

# Tests for adding agendas manually.
@pytest.mark.django_db
def test_agenda_creation(django_db_setup):
    '''
    Test that the same agenda url does not get added twice.
    '''
    event = Event.objects.get(ocd_id='ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d')
    document_obj, created = EventDocument.objects.get_or_create(event=event, url='https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081')
    assert not created == True

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import InMemoryUploadedFile

def test_agenda_pdf_form_submit():
    '''
    This unit test checks that a pdf validates the form.
    '''

    with open('lametro/tests/test_agenda.pdf', 'rb') as agenda:
        agenda_file = agenda.read()

        agenda_pdf_form = AgendaPdfForm(files={'agenda': SimpleUploadedFile('test_agenda.pdf', agenda_file, content_type='application/pdf')})
    
        assert agenda_pdf_form.is_valid() == True




@pytest.mark.django_db
def test_updates_made_true(django_db_setup):
    '''
    This test examines the relation between the System Safety, Security and Operations Committee meeting and its EventDocument (i.e., the agenda). 
    The Event was updated, after the Agenda was updated: the template tag should return True.
    '''
    event = Event.objects.get(ocd_id='ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d')
    assert updates_made(event.ocd_id) == True

@pytest.mark.django_db
def test_updates_made_false(django_db_setup):
    '''
    This test examines the relation between the Regular Board Meeting and its EventDocument. 
    The Event was not updated, after the Agenda was updated: the template tag should return False.
    '''
    event = Event.objects.get(ocd_id='ocd-event/c17e3544-dde3-4e40-8061-6163025298c7')
    assert updates_made(event.ocd_id) == False     

@pytest.mark.django_db
def test_related_bill_url(django_db_setup, client):
    '''
    This test checks that the bill detail view returns a successful response. 
    '''
    bill = Bill.objects.get(ocd_id='ocd-bill/1008870f-023e-4d5d-8626-fe00f043edd2')
    url = reverse('bill_detail', kwargs={'slug': bill.slug})
    response = client.get(url)

    assert response.status_code == 200

@pytest.mark.django_db
def test_related_bill_relation(django_db_setup, client):
    '''
    This test checks that a bill points to a related bill.
    '''
    bill = Bill.objects.get(ocd_id='ocd-bill/1008870f-023e-4d5d-8626-fe00f043edd2')
    related_bill = bill.related_bills.first()

    assert related_bill.related_bill_identifier == '2017-0443'



