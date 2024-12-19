from django.db.models.signals import post_save
from django.dispatch import receiver

from lametro.models import LAMetroPerson, Page, BoardMemberPage


@receiver(post_save, sender=LAMetroPerson)
def create_member_detail_page(sender, instance, created, **kwargs):
    page_exists = BoardMemberPage.objects.filter(person=instance).exists()

    if not page_exists:
        member_list = Page.objects.get(slug="metro-board-of-directors")

        detail_page = BoardMemberPage(
            person=instance,
            title=instance.name,
            slug=instance.slug,
            show_in_menus=False,
        )
        member_list.add_child(instance=detail_page)
        detail_page.save_revision().publish()
