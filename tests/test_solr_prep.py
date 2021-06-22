import pytest
from datetime import datetime, timedelta

from opencivicdata.legislative.models import EventParticipant

from lametro.search_indexes import LAMetroBillIndex

# @pytest.mark.parametrize('session_identifier,prepared_session', [
#     ('2014', '7/1/2014 to 6/30/2015'),
#     ('2015', '7/1/2015 to 6/30/2016'),
#     ('2016', '7/1/2016 to 6/30/2017'),
#     ('2017', '7/1/2017 to 6/30/2018'),
#     ('2018', '7/1/2018 to 6/30/2019'),
# ])
def test_legislative_session(bill, metro_organization, event, mocker):
    '''
    This test instantiates LAMetroBillIndex – a subclass of SearchIndex from
    Haystack, used for building the Solr index.

    The test, then, calls the SearchIndex `prepare` function, 
    which returns a dict of prepped data.
    https://github.com/django-haystack/django-haystack/blob/4910ccb01c31d12bf22dcb000894eece6c26f74b/haystack/indexes.py#L198
    '''
    # mock actions & agendas
    org1 = metro_organization.build()
    event1 = event.build()

    recent_action = {
            'date': datetime.now(),
            'description': 'org2 descripton',
            'event': event1,
            'organization': org1
        }
    older_action = {
            'date': datetime.now() - timedelta(days=365*5),
            'description': 'org2 descripton',
            'event': event1,
            'organization': org1
        }
    recent_agenda = {
            'date': datetime.now() - timedelta(days=365),
            'description': 'SCHEDULED',
            'event': event1,
            'organization': org1
        }
    older_agenda = {
            'date': datetime.now() - timedelta(days=365*5),
            'description': 'SCHEDULED',
            'event': event1,
            'organization': org1
        }
    test_cases = [[recent_action, older_action, recent_agenda, older_agenda], [recent_action, older_action], []]
    mock_actions_and_agendas = mocker.patch('lametro.models.LAMetroBill.actions_and_agendas',\
                                            new_callable=mocker.PropertyMock,\
                                            return_value=[recent_action, older_action, recent_agenda, older_agenda])

    bill = bill.build()

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert str(recent_agenda['date'].year) in indexed_data['legislative_session']

    mock_actions_and_agendas = mocker.patch('lametro.models.LAMetroBill.actions_and_agendas',\
                                            new_callable=mocker.PropertyMock,\
                                            return_value=[recent_action, older_action])
    assert str(recent_action['date'].year) in indexed_data['legislative_session']

    mock_actions_and_agendas = mocker.patch('lametro.models.LAMetroBill.actions_and_agendas',\
                                            new_callable=mocker.PropertyMock,\
                                            return_value=[])
    assert not indexed_data['legislative_session']


def test_sponsorships(bill, 
                      metro_organization,
                      event,
                      event_related_entity,
                      mocker):
    bill = bill.build()

    org1 = metro_organization.build()
    org2 = metro_organization.build()
    event1 = event.build()
    event1_participant = EventParticipant.objects.create(event=event1, name='Public Hearing')
    actions_and_agendas = [
        {
            'date': datetime.now(),
            'description': 'org1 description',
            'event': event1,
            'organization': org1
        },
        {
            'date': datetime.now(),
            'description': 'org2 descripton',
            'event': event1,
            'organization': org2
        },
        {
            'date': datetime.now(),
            'description': 'org2 descripton',
            'event': event1,
            'organization': org2
        },
        {
            'date': datetime.now(),
            'description': 'SCHEDULED',
            'event': event1,
            'organization': event1_participant
        }
    ]
    mock_actions_and_agendas = mocker.patch('lametro.models.LAMetroBill.actions_and_agendas',\
                                            new_callable=mocker.PropertyMock,\
                                            return_value=actions_and_agendas)

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert indexed_data['sponsorships'] == {org1.name, org2.name, 'Public Hearing'}
