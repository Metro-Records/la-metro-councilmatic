import pytest
from django.urls import reverse
from councilmatic.settings import OCD_CITY_COUNCIL_NAME

URLS_TO_TEST = [
    "lametro:index",
    "lametro:archive-search",
    "lametro:committees",
    "lametro:council_members",
    "lametro:event",
    "lametro:contact",
    "lametro:minutes",
    "lametro:search",
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
