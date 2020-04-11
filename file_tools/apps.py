from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FileToolsConfig(AppConfig):
    name = 'file_tools'
    verbose_name = _('File Tools')

    def ready(self):
    	import file_tools.signals
