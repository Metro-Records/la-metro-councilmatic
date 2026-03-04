from typing import Union, List
import logging
import requests

from django.db.models import QuerySet

from lametro.models.legislative import LAMetroBill

logger = logging.getLogger(__name__)


class BillService:
    @staticmethod
    def build_bills_notification(
        bills: Union[QuerySet, List[LAMetroBill]]
    ) -> requests.Response | None:
        """
        Return details on bill documents that need to be ocr'd,
        in order to send a notification to the Translation Suite.

        :return details: A list of dicts with document details
        """

        date_format = "%Y-%m-%d %H:%M:%S"
        details = []

        for b in bills:
            if board_report := b.board_report:
                details.append(
                    {
                        "title": b.friendly_name,
                        "source_url": board_report.url,
                        "created_at": b.created_at.strftime(date_format),
                        "updated_at": b.updated_at.strftime(date_format),
                        "document_type": "bill_version",
                        "document_id": str(board_report.pk),
                        "entity_type": "bill",
                        "entity_id": b.pk,
                    }
                )

        logger.info(f"Board reports found: {len(details)}")
        return details
