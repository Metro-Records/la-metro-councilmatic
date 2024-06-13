import pytest
from freezegun import freeze_time
from datetime import datetime, timezone, timedelta

from lametro.utils import get_url, LAMetroRequestTimeoutException


def test_get_url(mocker):
    ten_seconds_ago = datetime.now(tz=timezone.utc) - timedelta(seconds=20)
    with pytest.raises(LAMetroRequestTimeoutException):
        with freeze_time(ten_seconds_ago):
            get_url("https://google.com", timeout=5)

    one_second_ago = datetime.now(tz=timezone.utc) - timedelta(seconds=0)
    with freeze_time(one_second_ago):
        get_url("https://google.com", timeout=5)
