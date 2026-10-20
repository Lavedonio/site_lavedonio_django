from django.utils import translation

from .i18n import language_from_host


class DomainLocaleMiddleware:
    """
    Activates the language that matches the requested host (lavedonio.com ->
    English, lavedonio.com.br -> Portuguese), instead of relying on cookies,
    URL prefixes or the Accept-Language header like Django's LocaleMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = language_from_host(request.get_host())
        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()

        response = self.get_response(request)
        response.headers.setdefault('Content-Language', language)
        return response
