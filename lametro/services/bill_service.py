from typing import Union, List
import logging
import requests

from django.db.models import QuerySet
from django.conf import settings

from lametro.models.legislative import LAMetroBill

logger = logging.getLogger(__name__)


class BillService:
    @staticmethod
    def send_bills_notification(
        bills: Union[QuerySet, List[LAMetroBill]]
    ) -> requests.Response | None:
        """
        Send a notification to the Translation Suite with details
        on bill documents that need to be ocr'd.

        :return response: The response from the suite with a status code
        """

        url = f"https://{settings.TRANSLATION_SUITE_URL}/api/update-documents/"
        data = {"api_key": settings.TRANSLATION_API_KEY, "documents": []}
        date_format = "%Y-%m-%d %H:%M:%S"

        for b in bills:
            if board_report := b.board_report:
                data["documents"].append(
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

        logger.info(f"Board reports found: {len(data['documents'])}")
        if not data["documents"]:
            return None

        res = requests.post(
            url, json=data, headers={"Content-type": "application/json"}
        )
        return res
