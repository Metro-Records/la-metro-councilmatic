from django.templatetags.static import static
from django.utils.html import format_html, strip_tags

from html import unescape
from wagtail import hooks
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import Alert, EventNotice


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


class EventNoticeAdmin(ModelAdmin):
    model = EventNotice
    base_url_path = "event_notices"
    menu_icon = "comment"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    list_display = (
        "get_message",
        "broadcast_conditions",
        "get_comment_conditions",
    )
    list_filter = (
        "broadcast_conditions",
        "comment_conditions",
    )
    search_fields = (
        "broadcast_conditions",
        "comment_conditions",
        "message",
    )

    def get_message(self, obj):
        return strip_tags(unescape(obj.message))[:50]

    def get_comment_conditions(self, obj):
        return [cond.replace("_", " ") for cond in obj.comment_conditions]

    get_message.short_description = "Message"
    get_comment_conditions.short_description = "Comment conditions"


modeladmin_register(AlertAdmin)
modeladmin_register(EventNoticeAdmin)


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
    items.append(ModelAdminLink(AlertAdmin))
    return items


@hooks.register("insert_global_admin_js", order=500)
def insert_custom_wagtail_javascript():
    return format_html('<script src="{}"></script>', static("js/wagtail_custom.js"))


@hooks.register("insert_global_admin_css", order=500)
def insert_custom_wagtail_css():
    return format_html(
        '<link rel="stylesheet" href="{}"></script>', static("css/wagtail_custom.css")
    )
