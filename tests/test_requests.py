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


def test_timed_get_passes_timeout_to_requests(mocker, settings):
    """
    The trace function in timed_get can't fire while a socket is blocked, so
    requests must always get a timeout, even when the caller doesn't pass one.
    """
    mock_get = mocker.patch("lametro.utils.requests.get")

    timed_get("https://example.com")
    assert mock_get.call_args.kwargs["timeout"] == settings.REQUEST_TIMEOUT

    timed_get("https://example.com", timeout=2)
    assert mock_get.call_args.kwargs["timeout"] == 2
