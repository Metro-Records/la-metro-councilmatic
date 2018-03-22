import datetime

from django.core.urlresolvers import reverse
import pytest

from .conftest import get_uid_chunk
from lametro.views import LAMetroPerson


@pytest.mark.django_db
def test_person_page_redirects(client, metro_person, mocker):
    person = metro_person.build()

    # Patch a bunch of model attributes, because patching get_context_data
    # breaks the url routing, for some reason.

    mock_membership = mocker.patch('lametro.views.Membership', autospec=True)
    mock_membership.role = 'Superhero'

    mocker.patch.object(LAMetroPerson, 'latest_council_membership', return_value=mock_membership)

    mocker.patch.object(LAMetroPerson, 'current_council_seat', return_value=None)
    mocker.patch.object(LAMetroPerson, 'committee_sponsorships', return_value=[])

    # Assert navigating to a valid slug works.

    url = reverse('person', kwargs={'slug': person.slug})
    rv = client.get(url)

    assert rv.status_code == 200

    # Assert navigating to a partially valid slug, redirects to a valid slug.

    partial_slug = '-'.join(person.slug.split('-')[:-1])
    new_slug = '-'.join([partial_slug, get_uid_chunk()])

    url = reverse('person', kwargs={'slug': new_slug})
    rv = client.get(url)

    assert rv.status_code == 301

    # Assert navigating to a partially valid slug matching more than one
    # object returns a 404.

    person_of_same_name = metro_person.build()

    url = reverse('person', kwargs={'slug': partial_slug})
    rv = client.get(url)

    assert rv.status_code == 404

    # Assert navigating to a slug that does not exist returns a 404.

    url = reverse('person', kwargs={'slug': 'the-hulk'})
    rv = client.get(url)

    assert rv.status_code == 404
