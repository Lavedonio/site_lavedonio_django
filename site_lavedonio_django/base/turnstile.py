"""
Cloudflare Turnstile, which keeps bots from sending forms.

The widget in the page gives the visitor a token, sent with the form in the
"cf-turnstile-response" field, which is checked here with Cloudflare's
Siteverify API before the form is processed.
Docs: https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
"""
import json
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.http.request import split_domain_port

logger = logging.getLogger(__name__)

SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'

# Form field added by the widget
TOKEN_FIELD = 'cf-turnstile-response'

TOKEN_MAX_LENGTH = 2048

# Seconds, so a slow response doesn't keep the visitor waiting
SITEVERIFY_TIMEOUT = 10


def verify_turnstile(request, action):
    """
    Whether the visitor passed the challenge of the widget with `action` in a
    page of this same host. Any error counts as not passed.
    """
    token = request.POST.get(TOKEN_FIELD, '')
    if not token or len(token) > TOKEN_MAX_LENGTH:
        return False

    # The visitor's IP (remoteip) is optional and left out: behind a proxy,
    # REMOTE_ADDR isn't the visitor's IP
    data = urlencode({'secret': settings.TURNSTILE_SECRET_KEY, 'response': token}).encode()
    try:
        with urlopen(Request(SITEVERIFY_URL, data=data), timeout=SITEVERIFY_TIMEOUT) as response:
            result = json.load(response)
    except (OSError, ValueError):
        logger.exception("Couldn't validate the Turnstile token")
        return False

    if not isinstance(result, dict):
        return False

    error_codes = result.get('error-codes') or []
    if 'missing-input-secret' in error_codes or 'invalid-input-secret' in error_codes:
        logger.error('TURNSTILE_SECRET_KEY is missing or invalid')

    if result.get('success') is not True:
        return False

    # The test keys don't return the action, and the hostname is always
    # example.com. They're only accepted in development, so that using them in
    # production blocks the form instead of leaving it unprotected.
    if (result.get('metadata') or {}).get('result_with_testing_key'):
        return settings.DEBUG

    domain, _port = split_domain_port(request.get_host())
    return result.get('action') == action and result.get('hostname') == domain
