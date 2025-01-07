from django.apps import AppConfig


class LAMetroCouncilmaticConfig(AppConfig):
    name = "lametro"
    verbose_name = "LA Metro Councilmatic"

    def ready(self):
        import lametro.signals.handlers  # noqa
