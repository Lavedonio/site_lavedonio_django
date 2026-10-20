from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UploadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uploads'
    verbose_name = _('Uploads')
