import pytest

from django.urls import reverse
from freezegun import freeze_time


@freeze_time("2025-03-15 10:00:00")
@pytest.mark.parametrize(
    "expiration_str,should_display",
    [
        ("2025-03-20 10:00:00", True),
        ("2025-03-15 11:00:00", True),
        ("2025-03-15 09:00:00", False),
        ("2025-03-14 10:00:00", False),
    ],
)
def test_alert_expiration(client, alert, expiration_str, should_display):
    """
    Test that alerts do not show on the page when expired
    """
    test_alert = alert.build(expiration=expiration_str)
    url = reverse("lametro:index")
    response = client.get(url)

    assert (
        test_alert.description in response.content.decode("utf-8")
    ) == should_display
