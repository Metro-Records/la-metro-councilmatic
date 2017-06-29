from django.test import TestCase
from django.contrib import auth
from django.contrib.auth.models import User

from councilmatic_core.models import Event, EventDocument
from lametro.models import LAMetroEvent

class AgendaUploadTest(TestCase):
    # Test user creation
    def setUp(self):
        self.user_metro = User.objects.create(username='user_metro')
        self.event_metro = Event.objects.create(ocd_id='ocd-event/17fdaaa3-0aba-4df0-9893-2c2e8e94d18d',
          ocd_created_at='2017-05-27 11:10:46.574-05',
          ocd_updated_at='2017-05-27 11:10:46.574-05',
          name='System Safety, Security and Operations Committee',
          start_time='2017-05-18 12:15:00-05', 
          updated_at='2017-06-19 11:06:47.1853')
        self.agenda_url = 'https://metro.legistar.com/View.ashx?M=A&ID=545192&GUID=19F05A99-F3FB-4354-969F-67BE32A46081'

    def test_user_existence(self):
        assert self.user_metro

    # Test that the same agenda url does not get added twice.
    def test_scraped_agenda(self):
        document_obj, created = EventDocument.objects.get_or_create(event=self.event_metro, url=self.agenda_url)
        document_obj, created = EventDocument.objects.get_or_create(event=self.event_metro, url=self.agenda_url)
        assert not created == True

    def tearDown(self):
        self.user_metro.delete()
        self.event_metro.delete()

