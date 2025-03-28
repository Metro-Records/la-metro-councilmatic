import pytest

from django.urls import reverse
from freezegun import freeze_time

from lametro.models import Tooltip


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


@pytest.mark.parametrize(
    "disabled,should_display",
    [(False, True), (True, False)],
)
def test_tooltips_display(client, disabled, should_display, bill, metro_subject):
    """
    Test that tooltips display when their target is present, and when not disabled.
    """
    metro_subject.build(name="Kiosks")

    # Add this classification to make sure the bill is discoverable by the model manager
    test_bill = bill.build(classification=["Board Box"], subject=["Kiosks"])
    test_content = "A test tooltip for a subject!"
    Tooltip.objects.create(target="subject", content=test_content, disabled=disabled)

    url = reverse("lametro:bill_detail", kwargs={"slug": test_bill.slug})
    response = client.get(url)
    assert (test_content in response.content.decode("utf-8")) == should_display
