from django.db.models.signals import post_save
from django.dispatch import receiver

from lametro.models import LAMetroPerson, BoardMemberDetails


@receiver(post_save, sender=LAMetroPerson)
def create_member_details(sender, instance, created, **kwargs):
    details_exist = BoardMemberDetails.objects.filter(person=instance).exists()

    if not details_exist:
        BoardMemberDetails.objects.create(person=instance)
