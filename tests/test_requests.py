import pytest
from freezegun import freeze_time
from datetime import datetime, timezone, timedelta

from lametro.utils import timed_get, LAMetroRequestTimeoutException


def test_timed_get(mocker):
    ten_seconds_ago = datetime.now(tz=timezone.utc) - timedelta(seconds=20)
    with pytest.raises(LAMetroRequestTimeoutException):
        with freeze_time(ten_seconds_ago):
            timed_get("https://google.com", timeout=5)

    one_second_ago = datetime.now(tz=timezone.utc) - timedelta(seconds=1)
    with freeze_time(one_second_ago):
        timed_get("https://google.com", timeout=5)
