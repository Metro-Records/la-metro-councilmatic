from lametro.templatetags.lametro_extras import (
    inferred_status_label,
    bill_status_from_last_action,
)


def test_no_label_when_no_action():
    status = bill_status_from_last_action(None)
    html = inferred_status_label(status)

    assert html is None


def test_label_when_action():
    status = bill_status_from_last_action("adopTEd as amenDed")
    html = inferred_status_label(status)

    assert html == "<span class='label label-adopted'>Adopted</span>"
