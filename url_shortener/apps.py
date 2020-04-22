from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UrlShortenerConfig(AppConfig):
    name = 'url_shortener'
    verbose_name = _('URL Shortener')
