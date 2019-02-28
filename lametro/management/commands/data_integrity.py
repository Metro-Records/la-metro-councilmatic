import logging
import logging.config

from django.conf import settings

from councilmatic_core.management.commands import data_integrity
from lametro.models import LAMetroBill


logging.config.dictConfig(settings.LOGGING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("pysolr").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class Command(data_integrity.Command):
    '''
    Subclasses the data_integrity management command in django-councilmatic:
    https://github.com/datamade/django-councilmatic/blob/master/councilmatic_core/management/commands/data_integrity.py

    This command counts LAMetroBill objects, which undergo additional fiiltering 
    via the LAMetroBillManager.
    '''
    class Meta:
        proxy = True

    def count_councilmatic_bills(self):

        return LAMetroBill.objects.all().count()