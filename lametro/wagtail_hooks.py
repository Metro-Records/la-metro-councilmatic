from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Alert


class AlertAdmin(ModelAdmin):
    model = Alert
    base_url_path = "alerts"
    menu_icon = "warning"
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = ("content",)
    list_filter = ("type",)
    search_fields = (
        "type",
        "description",
    )


modeladmin_register(AlertAdmin)


class ModelAdminLink:
    def __init__(self, modeladmin_cls):
        self.modeladmin = modeladmin_cls()

    def render(self, request):
        return (
            f'<li class="w-userbar__item" role="presentation"><a href="{self.modeladmin.url_helper.index_url}" '
            + f'target="_parent" role="menuitem">Manage {self.modeladmin.get_menu_label()}</a></li>'
        )


@hooks.register("construct_wagtail_userbar")
def add_modeladmin_links(request, items):
    for modeladmin_cls in (AlertAdmin,):
        items.append(ModelAdminLink(modeladmin_cls))
    return items


@hooks.register("insert_global_admin_js", order=500)
def insert_custom_wagtail_javascript():
    return format_html('<script src="{}"></script>', static("js/wagtail_custom.js"))


@hooks.register("insert_global_admin_css", order=500)
def insert_custom_wagtail_css():
    return format_html(
        '<link rel="stylesheet" href="{}"></script>', static("css/wagtail_custom.css")
    )
