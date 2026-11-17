import logging

import elasticsearch
from haystack import connections
from haystack.backends.elasticsearch7_backend import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchEngine,
)

logger = logging.getLogger(__name__)

SEARCH_HIGHLIGHT_OPTIONS = {
    "fields": {"text": {}, "attachment_text": {}},
    "fragment_size": 200,
    "number_of_fragments": 1,
    # HTML-escape the source text, since snippets are rendered with |safe
    "encoder": "html",
}


class _ExcludeSourceFieldsClient:
    """
    Wraps an Elasticsearch client so search requests leave the given fields
    out of each hit's _source.

    Haystack always calls ``conn.search(..., _source=True)``, and that URL
    parameter overrides any ``_source`` filtering in the request body. The
    ``_source_excludes`` URL parameter still applies alongside it.
    """

    def __init__(self, client, excludes):
        self._client = client
        self._excludes = excludes

    def search(self, *args, **kwargs):
        kwargs.setdefault("_source_excludes", self._excludes)
        return self._client.search(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._client, name)


class LAMetroElasticsearchBackend(Elasticsearch7SearchBackend):
    """
    Customizes Haystack's Elasticsearch backend to:

    - Keep highlights for every field. Haystack only exposes highlights for
      the document field (``text``), so ``result.highlighted`` is instead the
      full Elasticsearch highlight dict, e.g.
      ``{"text": [...], "attachment_text": [...]}``.
    - Leave large full-text fields out of search responses. They can be
      megabytes per result and are only needed by Elasticsearch to match and
      highlight, not for rendering results. They are still indexed and stored.
    - Fall back to unhighlighted results when a matching document has a
      highlighted field longer than index.highlight.max_analyzed_offset
      (1M characters by default). Elasticsearch fails the whole search in
      that case, and versions before 7.12 can't cap it per request.
    """

    EXCLUDED_SOURCE_FIELDS = ["text", "full_text", "ocr_full_text", "attachment_text"]

    def __init__(self, connection_alias, **connection_options):
        super().__init__(connection_alias, **connection_options)
        self.conn = _ExcludeSourceFieldsClient(self.conn, self.EXCLUDED_SOURCE_FIELDS)

    def search(self, query_string, **kwargs):
        try:
            return super().search(query_string, **kwargs)
        except elasticsearch.RequestError as e:
            if not kwargs.get("highlight") or "max_analyzed_offset" not in str(e.info):
                raise

            logger.warning(
                "Search for %r matched a document too long to highlight; "
                "returning results without highlighting.",
                query_string,
            )
            return super().search(query_string, **{**kwargs, "highlight": False})

    def _process_results(self, raw_results, *args, **kwargs):
        content_field = (
            connections[self.connection_alias].get_unified_index().document_field
        )

        hits = raw_results.get("hits", {}).get("hits", [])

        if any("highlight" in hit for hit in hits):
            # The parent class sets result.highlighted to
            # raw_result["highlight"][content_field], so nest the full
            # highlight dict under the content field to pass it through.
            raw_results = {
                **raw_results,
                "hits": {
                    **raw_results["hits"],
                    "hits": [
                        (
                            {**hit, "highlight": {content_field: hit["highlight"]}}
                            if "highlight" in hit
                            else hit
                        )
                        for hit in hits
                    ],
                },
            }

        return super()._process_results(raw_results, *args, **kwargs)


class LAMetroElasticsearchEngine(Elasticsearch7SearchEngine):
    backend = LAMetroElasticsearchBackend
