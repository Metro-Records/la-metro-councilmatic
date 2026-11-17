from haystack import connections
from haystack.backends.elasticsearch7_backend import (
    Elasticsearch7SearchBackend,
    Elasticsearch7SearchEngine,
)

SEARCH_HIGHLIGHT_OPTIONS = {
    "fields": {"text": {}, "attachment_text": {}},
    "fragment_size": 200,
    "number_of_fragments": 1,
    # HTML-escape the source text, since snippets are rendered with |safe
    "encoder": "html",
    # attachment_text can be very long. Only analyze the first 1M characters
    # (the index default limit) instead of erroring on longer fields.
    "max_analyzed_offset": 1000000,
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
    """

    EXCLUDED_SOURCE_FIELDS = ["text", "full_text", "ocr_full_text", "attachment_text"]

    def __init__(self, connection_alias, **connection_options):
        super().__init__(connection_alias, **connection_options)
        self.conn = _ExcludeSourceFieldsClient(self.conn, self.EXCLUDED_SOURCE_FIELDS)

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
