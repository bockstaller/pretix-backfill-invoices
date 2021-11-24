from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.0.0"


class PluginApp(PluginConfig):
    name = "pretix_backfill_invoices"
    verbose_name = "Backfill invoices"

    class PretixPluginMeta:
        name = gettext_lazy("Backfill invoices")
        author = "Lukas Bockstaller"
        description = gettext_lazy("Django Admin command to backfill missing invoices")
        visible = True
        version = __version__
        category = "FEATURE"
        compatibility = "pretix>=4.3.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = "pretix_backfill_invoices.PluginApp"
