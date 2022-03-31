from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from councilmatic_core.models import Event as CouncilmaticEvent
from lametro.models import LAMetroEvent



@receiver(post_save, sender=CouncilmaticEvent)
def create_lametro_event(sender, instance, created, **kwargs):
    if created:
        LAMetroEvent.objects.create(event=instance)
