import pytest

from councilmatic_core.models import Event, EventDocument
from lametro.models import LAMetroEvent
from lametro.templatetags.lametro_extras import updates_made

# Test that the same agenda url does not get added twice.
@pytest.mark.django_db
def test_agenda_creation(django_db_setup):
    event = Event.objects.get(ocd_id='ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d')
    document_obj, created = EventDocument.objects.get_or_create(event=event, url='https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081')
    assert not created == True

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

