"""
Domain based internationalization helpers.

Each language is served from its own host (see settings.LANGUAGE_DOMAINS), e.g.
lavedonio.com for English and lavedonio.com.br for Brazilian Portuguese. These
helpers map hosts to languages and build the equivalent URL of a page in the
other languages.
"""
from django.conf import settings
from django.http.request import split_domain_port
from django.urls import translate_url
from django.utils import translation


# Query string flag added to the language switcher links, so the destination
# page knows the visitor picked that language on purpose and doesn't offer to
# switch back based on the browser settings.
LANGUAGE_CHOSEN_PARAM = 'lang_chosen'


def get_language_codes():
    return [code for code, _name in settings.LANGUAGES]


def get_language_choices():
    # Used as a callable in model fields, so adding a language to
    # settings.LANGUAGES doesn't require a new migration
    return settings.LANGUAGES


def get_language_name(code):
    """Name of the language in itself, e.g. 'Português (Brasil)'. Used in the language menu."""
    return dict(settings.LANGUAGES).get(code, code)


def get_language_display_name(code):
    """Name of the language in the active language, e.g. 'Brazilian Portuguese'. Used in sentences."""
    try:
        return translation.get_language_info(code)['name_translated']
    except KeyError:
        return get_language_name(code)


def get_language_short_name(code):
    """'en' -> 'EN', 'pt-br' -> 'PT-BR'"""
    return code.upper()


def normalize_host(host):
    domain, _port = split_domain_port(host)
    domain = domain.lower()
    if domain.startswith('www.'):
        domain = domain[len('www.'):]
    return domain


def language_from_host(host):
    domain = normalize_host(host)
    for code, language_domain in settings.LANGUAGE_DOMAINS.items():
        if language_domain.lower() == domain:
            return code
    return settings.LANGUAGE_CODE


def get_fallback_languages(language=None):
    """
    Languages to try, in order, when some content isn't available in
    `language`: the language itself, then the default one, then the rest.
    """
    language = language or translation.get_language() or settings.LANGUAGE_CODE
    ordered = [language, settings.LANGUAGE_CODE] + get_language_codes()
    return list(dict.fromkeys(ordered))


def build_language_url(request, language, path):
    """Absolute URL of `path` on the host that serves `language`."""
    domain = settings.LANGUAGE_DOMAINS.get(language)
    if not domain:
        return request.build_absolute_uri(path)

    host = request.get_host()
    _domain, port = split_domain_port(host)

    # Keeps the "www." prefix and the port (local development) of the current host
    if host.lower().startswith('www.'):
        domain = f'www.{domain}'
    if port:
        domain = f'{domain}:{port}'

    return f'{request.scheme}://{domain}{path}'


def get_path_without_language_flag(request):
    query = request.GET.copy()
    query.pop(LANGUAGE_CHOSEN_PARAM, None)
    return f'{request.path}?{query.urlencode()}' if query else request.path


def get_language_alternates(request, paths=None):
    """
    List with the equivalent of the current page in every available language.

    `paths` maps language codes to paths. When omitted, the current path is
    translated to every language using the i18n URL patterns. Views that only
    have some of the languages available (like blog posts) pass just those.
    The current language is always included (for the language menu), but with
    `is_available=False` if the page isn't really available in it.
    """
    current_language = translation.get_language()
    current_path = get_path_without_language_flag(request)

    if paths is None:
        paths = {code: translate_url(current_path, code) for code in get_language_codes()}

    alternates = []
    for code in get_language_codes():
        is_available = code in paths
        if not is_available and code != current_language:
            continue

        url = build_language_url(request, code, paths.get(code, current_path))
        separator = '&' if '?' in url else '?'
        alternates.append({
            'code': code,
            'name': get_language_name(code),
            'short_name': get_language_short_name(code),
            'url': url,
            'switch_url': f'{url}{separator}{LANGUAGE_CHOSEN_PARAM}=1',
            'is_current': code == current_language,
            'is_available': is_available,
        })

    return alternates
