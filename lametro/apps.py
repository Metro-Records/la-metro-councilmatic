from councilmatic_core.apps import CouncilmaticConfig


class LAMetroCouncilmaticConfig(CouncilmaticConfig):
    name = 'lametro'
    verbose_name = "LA Metro Councilmatic"

    def ready(self):
        super().ready()
        import lametro.signals.handlers
