import datetime

from django.urls import reverse, resolve
import pytest

from .conftest import get_uid_chunk
from lametro.views import PersonDetailView, LAPersonDetailView


@pytest.mark.django_db
def test_person_page_redirects(client, metro_person, mocker):
    person = metro_person.build()

    response = mocker.Mock()
    response.status_code = 200

    # The purpose of this test is to make sure we are handling different
    # routing cases appropriately, not that particular contents of a
    # returned view. So, in the case of a happy routing, we'll mock
    # the response of a successful dispatch
    mocker.patch.object(PersonDetailView, 'dispatch', return_value=response)

    # Assert navigating to a valid slug works.

    view = LAPersonDetailView()
    view.kwargs = {'slug': person.slug}

    response = view.dispatch(None)
    assert response.status_code == 200

    # Assert navigating to a partially valid slug, redirects to a valid slug.

    partial_slug = '-'.join(person.slug.split('-')[:-1])
    new_slug = '-'.join([partial_slug, get_uid_chunk()])

    view = LAPersonDetailView()
    view.kwargs = {'slug': new_slug}
    # Assert navigating to a valid slug works.

    response = view.dispatch(None)
    assert response.status_code == 301

    # Assert navigating to a partially valid slug matching more than one
    # object returns a 404.

    person_of_same_name = metro_person.build()

    view = LAPersonDetailView()
    view.kwargs = {'slug': partial_slug}

    response = view.dispatch(None)
    assert response.status_code == 404

    # Assert navigating to a slug that does not exist returns a 404.

    view = LAPersonDetailView()
    view.kwargs = {'slug': 'the-hulk'}
    # Assert navigating to a valid slug works.

    response = view.dispatch(None)
    assert response.status_code == 404
