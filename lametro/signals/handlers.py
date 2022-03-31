from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from councilmatic_core.models import Event as CouncilmaticEvent
from lametro.models import LAMetroEvent



@receiver(post_save, sender=CouncilmaticEvent)
def create_lametro_event(sender, instance, created, **kwargs):
    if created:
        lametro_event = LAMetroEvent.objects(event_ptr=instance.event_id)

        # Save the LAMetroEvent, but not the related parent Event
        lametro_event.save_base(raw=True)
