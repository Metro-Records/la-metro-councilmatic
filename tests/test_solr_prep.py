import pytest
from datetime import datetime

from lametro.search_indexes import LAMetroBillIndex

@pytest.mark.parametrize('session_identifier,prepared_session', [
    ('2014', '7/1/2014 to 6/30/2015'),
    ('2015', '7/1/2015 to 6/30/2016'),
    ('2016', '7/1/2016 to 6/30/2017'),
    ('2017', '7/1/2017 to 6/30/2018'),
    ('2018', '7/1/2018 to 6/30/2019'),
])
def test_legislative_session(bill, 
                             legislative_session,
                             session_identifier,
                             prepared_session):
    '''
    This test instantiates LAMetroBillIndex – a subclass of SearchIndex from
    Haystack, used for building the Solr index.

    The test, then, calls the SearchIndex `prepare` function, 
    which returns a dict of prepped data.
    https://github.com/django-haystack/django-haystack/blob/4910ccb01c31d12bf22dcb000894eece6c26f74b/haystack/indexes.py#L198
    '''
    legislative_session.identifier = session_identifier
    legislative_session.save()
    bill = bill.build(legislative_session=legislative_session)

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert indexed_data['legislative_session'] == prepared_session

def test_sponsorships(bill, 
                      metro_organization,
                      event,
                      mocker):
    bill = bill.build()

    org1 = metro_organization.build()
    org2 = metro_organization.build()
    event1 = event.build()
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
        }
    ]
    mock_actions_and_agendas = mocker.patch('lametro.models.LAMetroBill.actions_and_agendas',\
                                            new_callable=mocker.PropertyMock,\
                                            return_value=actions_and_agendas)

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert indexed_data['sponsorships'] == {org1.name, org2.name}
