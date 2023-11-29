from django.contrib import admin  # noqa
from lametro.models import Alert


class AlertAdmin(admin.ModelAdmin):
    list_display = ("type", "description")


admin.site.register(Alert, AlertAdmin)
