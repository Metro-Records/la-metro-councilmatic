from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.contrib.typed_table_block.blocks import TypedTableBlock


class NavigationBlock(blocks.StaticBlock):
    class Meta:
        template = "lametro/blocks/navigation.html"
        icon = "bars"

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)

        context["navigation_items"] = {
            section.value["heading"] or "Unnamed Section": section.value["anchor"]
            for section in kwargs["parent_context"]["page"].body
            if section.value["anchor"]
        }

        return context


class ContentBlock(blocks.StreamBlock):
    text = blocks.RichTextBlock()
    image = ImageChooserBlock()
    table = TypedTableBlock(
        [
            ("rich_text", blocks.RichTextBlock()),
        ]
    )
    navigation = NavigationBlock()


class ArticleBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=False)
    content = ContentBlock()
    anchor = blocks.CharBlock(
        required=False, help_text="Add anchor to enable direct links to this section"
    )
