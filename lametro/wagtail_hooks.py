from django.contrib import admin  # noqa
from django.contrib.admin import SimpleListFilter
from django.templatetags.static import static
from django.utils.html import format_html

from wagtail import hooks
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from lametro.models import Alert, BoardMemberPage


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


class MembershipStatusFilter(SimpleListFilter):
    title = "membership status"
    parameter_name = "current"

    def lookups(self, request, model_admin):
        return [
            ("true", "Has current memberships"),
            ("false", "Does not have current memberships"),
        ]

    def queryset(self, request, queryset):
        if self.value():
            if not self.value() in ("true", "false"):
                return queryset.none()

            people = [
                page.person
                for page in BoardMemberPage.objects.select_related("person")
                .prefetch_related("person__memberships")
                .distinct()
            ]

            if self.value() == "true":
                filter_func = lambda person: person.current_memberships.exists()  # noqa
            else:
                filter_func = (
                    lambda person: not person.current_memberships.exists()
                )  # noqa

            return queryset.filter(
                person__id__in=(p.id for p in filter(filter_func, people))
            )


class BoardMemberPageAdmin(ModelAdmin):
    model = BoardMemberPage
    list_display = (
        "member",
        "current_memberships",
    )
    list_select_related = ("person",)
    list_filter = (MembershipStatusFilter,)

    @admin.display
    def member(self, obj):
        return obj.person.name

    @admin.display(empty_value="")
    def current_memberships(self, obj):
        if (
            current_memberships := obj.person.current_memberships.order_by(
                "organization__name"
            )
            .distinct()
            .values_list("organization__name", flat=True)
        ):
            organizations = "\n".join(f"<li>{org}</li>" for org in current_memberships)
            return format_html(f"<ul>{organizations}</ul>")


modeladmin_register(AlertAdmin)
modeladmin_register(BoardMemberPageAdmin)


class ModelAdminLink:
    def __init__(self, modeladmin_cls):
        self.modeladmin = modeladmin_cls()

    def render(self, request):
        return format_html(
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
