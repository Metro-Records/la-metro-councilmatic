import pytest

from django.urls import reverse

from councilmatic_core.models import Organization

def test_organization_url(client, metro_organization):
    '''
    This test checks that the committee detail view returns a successful response. 
    '''
    organization = metro_organization.build()
    url = reverse('lametro:committee', kwargs={'slug': organization.slug})
    response = client.get(url)

    assert response.status_code == 200

def test_membership_context(client, metro_organization, membership, metro_person):
    '''
    This test checks that the `memberships_object` contains the expected number of memberships in the correct order.
    '''
    organization = metro_organization.build()

    membership_info = {
        'organization': organization,
        'role': 'Vice Chair',
    }
    chair_membership = membership.build(**membership_info)

    new_member = metro_person.build()
    membership_info = {
        'person': new_member,
        'organization': organization,
        'role': 'Chair',
    }
    vice_chair_membership = membership.build(**membership_info)

    new_member = metro_person.build()
    membership_info = {
        'person': new_member,
        'organization': organization,
        'role': 'Member',
    }
    regular_membership = membership.build(**membership_info)

    url = reverse('committee_detail', kwargs={'slug': organization.slug})
    response = client.get(url)

    memberships = response.context['non_ceos']

    assert len(memberships) == 3

    assert memberships[0].role == 'Chair'
    assert memberships[1].role == 'Vice Chair'
    assert memberships[2].role == 'Member'
