import pytest
from haystack import connections
from haystack.inputs import Raw
from haystack.query import SearchQuerySet

from lametro.search_backend import (
    SEARCH_HIGHLIGHT_OPTIONS,
    LAMetroElasticsearchBackend,
)
from lametro.search_indexes import LAMetroBillIndex


# Helper fixtures that construct raw Elasticsearch responses
def _raw_hit(django_id, highlight=None):
    hit = {
        "_score": 1.0,
        "_source": {
            "django_ct": "lametro.lametrobill",
            "django_id": str(django_id),
            "identifier": f"2024-000{django_id}",
        },
    }
    if highlight is not None:
        hit["highlight"] = highlight
    return hit


def _raw_results(*hits):
    return {"hits": {"total": {"value": len(hits)}, "hits": list(hits)}}


def test_backend_exposes_all_highlighted_fields():
    backend = connections["default"].get_backend()

    raw_results = _raw_results(
        _raw_hit(1, {"text": ["a <em>bus</em> lane"]}),
        _raw_hit(2, {"attachment_text": ["new <em>bus</em> shelters"]}),
        _raw_hit(3),
    )

    results = backend._process_results(raw_results, highlight=True)["results"]

    assert results[0].highlighted == {"text": ["a <em>bus</em> lane"]}
    assert results[1].highlighted == {"attachment_text": ["new <em>bus</em> shelters"]}
    assert not results[2].highlighted

    # Our search backend shouldn't change the raw results from Elasticsearch
    # after highlighting
    assert raw_results["hits"]["hits"][0]["highlight"] == {
        "text": ["a <em>bus</em> lane"]
    }


def test_highlight_options_sent_to_elasticsearch():
    backend = connections["default"].get_backend()

    kwargs = backend.build_search_kwargs("bus", highlight=SEARCH_HIGHLIGHT_OPTIONS)

    assert kwargs["highlight"]["fields"] == {"text": {}, "attachment_text": {}}
    assert kwargs["highlight"]["encoder"] == "html"


@pytest.fixture
def indexed_bill(bill):
    bill = bill.build()
    bill.documents.create(
        note="Attachment A",
        date="2017-06-09",
        extras={"full_text": "Install new bus shelters at Union Station."},
    )

    index = LAMetroBillIndex()
    index.update_object(bill)

    yield bill

    index.remove_object(bill)


def test_search_highlights_without_returning_full_text(indexed_bill):
    results = list(
        SearchQuerySet()
        .filter(attachment_text=Raw("shelters"))
        .highlight(**SEARCH_HIGHLIGHT_OPTIONS)
    )

    result = next(r for r in results if r.pk == str(indexed_bill.pk))

    assert result.highlighted["attachment_text"] == [
        "Install new bus <em>shelters</em> at Union Station."
    ]

    # Large full-text fields are excluded from the response...
    returned_fields = result.get_additional_fields()
    for field in LAMetroElasticsearchBackend.EXCLUDED_SOURCE_FIELDS:
        assert field not in returned_fields

    # ...but fields needed to render the result are still there
    assert result.slug == indexed_bill.slug
