import logging

from lametro.models.legislative import LAMetroBill

logger = logging.getLogger(__name__)


class BillService:
    @staticmethod
    def build_bill_notification(bill: LAMetroBill) -> dict:
        """
        Return details on a bill's document that needs to be ocr'd,
        in order to send a notification to the Translation Suite.

        :return details: A dict with document details if available
        """

        date_format = "%Y-%m-%d %H:%M:%S"
        details = {}

        if board_report := bill.board_report:
            details = {
                "title": bill.friendly_name,
                "source_url": board_report.url,
                "created_at": bill.created_at.strftime(date_format),
                "updated_at": bill.updated_at.strftime(date_format),
                "document_type": "bill_version",
                "document_id": str(board_report.pk),
                "entity_type": "bill",
                "entity_id": bill.pk,
            }

        return details
