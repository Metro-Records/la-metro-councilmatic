import pytest

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
    bill = bill.build(_legislative_session=legislative_session)

    index = LAMetroBillIndex()
    indexed_data = index.prepare(bill)

    assert indexed_data['legislative_session'] == prepared_session
