from django.conf import settings
from django.utils import translation
from django.utils.translation import gettext as _

from .i18n import LANGUAGE_CHOSEN_PARAM, get_language_alternates

# Cookie that stores whether the visitor allowed optional (analytics) cookies
COOKIE_CONSENT_NAME = 'cookie_consent'
COOKIE_CONSENT_VALUES = ('accepted', 'rejected')


def site_languages(request):
    """
    Data for the language switcher, the hreflang links and the "this page is
    also available in..." banner.

    Views whose content isn't available in every language (or whose URL changes
    between languages, like blog post slugs) set `request.language_alternate_paths`
    to a {language_code: path} dict before rendering.
    """
    alternates = get_language_alternates(request, getattr(request, 'language_alternate_paths', None))
    current_language = translation.get_language()

    # Banner texts are shown in the language being offered, so they are
    # rendered with that language active
    banner = {}
    for alternate in alternates:
        if alternate['is_current']:
            continue

        with translation.override(alternate['code']):
            banner[alternate['code']] = {
                'url': alternate['switch_url'],
                # Translators: shown to visitors whose browser is set to your language, offering
                # them the site in your language. Replace "English" by the name of your language.
                'message': _('This page is also available in English.'),
                # Translators: replace "English" by the name of your language.
                'action': _('Switch to English'),
                'dismiss': _('Dismiss'),
            }

    default_alternate = next((a for a in alternates if a['code'] == settings.LANGUAGE_CODE and a['is_available']), None)

    return {
        'language_alternates': alternates,
        'language_alternate_default': default_alternate,
        'language_banner': {
            'current': current_language,
            'default': settings.LANGUAGE_CODE,
            'chosenParam': LANGUAGE_CHOSEN_PARAM,
            'alternates': banner,
        },
    }


def cookie_consent(request):
    """The visitor's choice about optional cookies, for the navbar menu, the consent banner and analytics."""
    consent = request.COOKIES.get(COOKIE_CONSENT_NAME)
    if consent not in COOKIE_CONSENT_VALUES:
        consent = None

    return {
        'analytics_id': settings.ANALYTICS_ID,
        'cookie_consent': consent,
        'cookie_settings': {
            'cookieName': COOKIE_CONSENT_NAME,
            'consent': consent,
            'analyticsId': settings.ANALYTICS_ID,
        },
    }
