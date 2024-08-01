from haystack.backends import log_query
from haystack.backends.elasticsearch7_backend import (
    Elasticsearch7SearchBackend,
)
from haystack.backends.elasticsearch7_backend import Elasticsearch7SearchEngine
from haystack.models import SearchResult

import elasticsearch


class CustomElasticBackend(Elasticsearch7SearchBackend):
    @log_query
    def search(self, query_string, **kwargs):
        if len(query_string) == 0:
            return {"results": [], "hits": 0}

        if not self.setup_complete:
            self.setup()

        search_kwargs = self.build_search_kwargs(query_string, **kwargs)
        search_kwargs["from"] = kwargs.get("start_offset", 0)

        order_fields = set()
        for order in search_kwargs.get("sort", []):
            for key in order.keys():
                order_fields.add(key)

        geo_sort = "_geo_distance" in order_fields

        end_offset = kwargs.get("end_offset")
        start_offset = kwargs.get("start_offset", 0)
        if end_offset is not None and end_offset > start_offset:
            search_kwargs["size"] = end_offset - start_offset

        try:
            raw_results = self.conn.search(
                body=search_kwargs,
                index=self.index_name,
                _source=True,
                _source_excludes=[
                    "full_text",
                    "text",
                    "ocr_full_text",
                    "attachment_text",
                ],
                **self._get_doc_type_option(),
            )
        except elasticsearch.TransportError:
            if not self.silently_fail:
                raise

            self.log.exception(
                "Failed to query Elasticsearch using '%s'",
                query_string,
            )
            raw_results = {}

        return self._process_results(
            raw_results,
            highlight=kwargs.get("highlight"),
            result_class=kwargs.get("result_class", SearchResult),
            distance_point=kwargs.get("distance_point"),
            geo_sort=geo_sort,
        )


class CustomElasticEngine(Elasticsearch7SearchEngine):
    backend = CustomElasticBackend
