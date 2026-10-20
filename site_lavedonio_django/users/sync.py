"""
Keeps the visitor logged in (or out) on the hosts of every language.

Each language has its own domain (lavedonio.com and lavedonio.com.br), and
browsers keep a separate session cookie for each one. So, after logging in or
out on one of them, the visitor is redirected through the others with a signed
token, valid for one minute and only once, and then to where they were going.
"""
import secrets

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.urls import reverse
from django.utils.http import urlencode

from base.i18n import build_language_url, language_from_host

LOGIN = 'login'
LOGOUT = 'logout'

TOKEN_SALT = 'users.sync'
TOKEN_MAX_AGE = 60  # seconds


def get_other_languages(request):
    current = language_from_host(request.get_host())
    return [code for code in settings.LANGUAGE_DOMAINS if code != current]


def get_sync_url(request, action, user, next_url, languages=None):
    """
    URL of the next host to log in or out (`action`), which then continues to
    the following ones and, at the end, to `next_url` (an absolute URL).
    It's `next_url` itself when there are no other hosts.
    """
    if languages is None:
        languages = get_other_languages(request)
    if not languages or user is None:
        return next_url

    token = signing.dumps({
        'action': action,
        'user': user.pk,
        # Invalidates the token if the password changes in the meantime
        'hash': user.get_session_auth_hash(),
        'next': next_url,
        'languages': languages,
        'nonce': secrets.token_urlsafe(16),
    }, salt=TOKEN_SALT)
    path = f"{reverse('users:sync')}?{urlencode({'token': token})}"
    return build_language_url(request, languages[0], path)


def read_token(token):
    """Data of a valid, unused token. Raises signing.BadSignature otherwise."""
    data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)

    # Each token works only once. With several server processes, this needs a
    # cache shared by them (e.g. database or Redis) to be enforced across all of them.
    if not cache.add(f'users-sync-nonce:{data["nonce"]}', True, TOKEN_MAX_AGE):
        raise signing.BadSignature('Token already used.')
    return data
