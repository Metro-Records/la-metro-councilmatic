import pytest
from django.urls import reverse
from councilmatic.settings import OCD_CITY_COUNCIL_NAME

URLS_TO_TEST = [
    "lametro:index",
    "lametro:archive-search",
    "lametro:committees",
    "lametro:council_members",
    "lametro:events",
    "lametro:contact",
    "lametro:minutes",
    "lametro:search",
    "pdfviewer",
]


@pytest.mark.current
@pytest.mark.django_db
@pytest.mark.parametrize("url_name", URLS_TO_TEST)
def test_urls_accessibility(
    client,
    metro_organization,
    metro_person,
    event,
    url_name,
):
    """Test that all URLs are accessible and return a 200 status code."""

    # Put some initial data in the db
    _ = metro_organization.build(name=OCD_CITY_COUNCIL_NAME)
    _ = metro_person.build()
    _ = event.build()

    url = reverse(url_name)
    response = client.get(url)
    assert response.status_code == 200, f"{url} should return 200 status code"


@pytest.mark.django_db
def test_search_with_query_renders_results_header(client):
    url = reverse("lametro:search")
    response = client.get(url, {"q": "mobility"})

    assert response.status_code == 200
    assert b"mobility" in response.content


@pytest.mark.django_db
def test_council_members_renders_board_members(client, metro_organization, membership):
    """
    Create membership and make sure that we actually get content, not empty template.
    """
    board = metro_organization.build(name=OCD_CITY_COUNCIL_NAME)
    person = membership.build(organization=board, role="Board Member").person

    url = reverse("lametro:council_members")
    response = client.get(url)

    assert response.status_code == 200
    assert person.name.encode() in response.content
    assert f"/person/{person.slug}/".encode() in response.content
