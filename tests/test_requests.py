import pytest

from lametro.utils import timed_get, LAMetroRequestTimeoutException


def test_timed_get(mocker):
    """
    First run mocks time.time() so that it looks like 9 seconds have passed.
    Second run uses real time.
    """
    mocker.patch("lametro.utils.time.time", side_effect=[0, 9])

    with pytest.raises(LAMetroRequestTimeoutException):
        timed_get("https://google.com", timeout=5)

    mocker.stopall()
    timed_get("https://google.com", timeout=5)
