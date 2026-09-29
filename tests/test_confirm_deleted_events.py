from lametro.management.commands.confirm_deleted_events import check_deleted


def test_check_deleted_returns_correct_values():
    """
    Return False for existing URLs, True for non-existent URLs
    """

    real_url = "https://webapi.legistar.com/v1/metro/events/3539/"
    assert check_deleted(real_url) is False

    made_up_url = "https://webapi.legistar.com/metro/v1/events/999999999999999/"
    assert check_deleted(made_up_url) is True
