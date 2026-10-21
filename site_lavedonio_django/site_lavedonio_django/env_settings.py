"""
This file contains environment-specific settings configurations, in order to
isolate them from the default Django settings.py file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / '.env')

# Cloudflare's Turnstile test keys: the widget always passes. Only accepted
# with DEBUG on (see base/turnstile.py).
# Docs: https://developers.cloudflare.com/turnstile/troubleshooting/testing/
TURNSTILE_TEST_SITE_KEY = '1x00000000000000000000AA'
TURNSTILE_TEST_SECRET_KEY = '1x0000000000000000000000000000000AA'


def server_database():
    """
    The database of staging and production: PostgreSQL on the data VPS, reached
    over TLS, with each environment's tables in its own schema (DB_SCHEMA) of
    the same database. See deploy/README.md.
    """
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': str(os.environ['DB_NAME']),
            'USER': str(os.environ['DB_USER']),
            'PASSWORD': str(os.environ['DB_PASSWORD']),
            'HOST': str(os.environ['DB_HOST']),
            'PORT': str(os.environ.get('DB_PORT', 5432)),
            'OPTIONS': {
                'sslmode': os.environ.get('DB_SSLMODE', 'verify-full'),
                'sslrootcert': str(os.environ['DB_SSLROOTCERT']),
                'options': f"-c search_path={os.environ['DB_SCHEMA']}",
            },
            # The database is on another server: reuse connections between requests
            'CONN_MAX_AGE': 60,
            'CONN_HEALTH_CHECKS': True,
        }
    }


def r2_media_storage():
    """
    Uploads (covers, editor images...) in a Cloudflare R2 bucket, through its S3
    API, served by Cloudflare from the bucket's custom domain (MEDIA_DOMAIN).
    """
    return {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': str(os.environ['R2_BUCKET']),
            'endpoint_url': f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            'access_key': str(os.environ['R2_ACCESS_KEY_ID']),
            'secret_key': str(os.environ['R2_SECRET_ACCESS_KEY']),
            'region_name': 'auto',
            'custom_domain': str(os.environ['MEDIA_DOMAIN']),
            'url_protocol': 'https:',
            # The bucket is public through its domain, so URLs don't need signing
            'querystring_auth': False,
            # Like on a local disk: a new file never replaces another with the same name
            'file_overwrite': False,
            # So names never change content, and Cloudflare and browsers can keep them
            'object_parameters': {'CacheControl': 'public, max-age=31536000'},
        },
    }


class BaseSettings:

    def __init__(self) -> None:
        self.BASE_DIR = BASE_DIR
        self.SECRET_KEY = str(os.environ['SECRET_KEY'])
        self.DEBUG = str(os.environ['DEBUG_VALUE']) == 'True'
        self.ALLOWED_HOSTS = []
        self.DATABASES = {}

        # Where uploads are kept, and the URL they're served from
        self.MEDIA_STORAGE = {'BACKEND': 'django.core.files.storage.FileSystemStorage'}
        self.MEDIA_URL = 'media/'

        # Behind HTTPS (staging and production): secure cookies, HSTS and so on.
        # HSTS_SECONDS is how long browsers keep refusing plain HTTP.
        self.HTTPS = False
        self.HSTS_SECONDS = 0

        # Asks search engines not to index the site (staging)
        self.NOINDEX = False

        # Only shows the site to who's logged in (staging)
        self.LOGIN_REQUIRED = False

        # Kept in the database, so it's shared by every server process, which
        # the single-use tokens need (Turnstile and the login sync). Its table
        # is created with `python manage.py createcachetable`.
        self.CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'django_cache',
            }
        }

        # Which host serves each language ("www." prefixes are ignored).
        # Requests to any other host are served in LANGUAGE_CODE.
        self.LANGUAGE_DOMAINS = {}

        # Google Analytics measurement ID (optional). It's only loaded for
        # visitors who allow cookies.
        self.ANALYTICS_ID = os.environ.get('ANALYTICS_ID') or None

        # E-mail sent by the contact form, from DEFAULT_FROM_EMAIL to
        # CONTACT_EMAIL, through an SMTP server.
        self.EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
        self.EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
        self.EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
        self.EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
        self.EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
        self.EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
        self.DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL') or self.EMAIL_HOST_USER or 'webmaster@localhost'
        self.CONTACT_EMAIL = os.environ.get('CONTACT_EMAIL') or self.DEFAULT_FROM_EMAIL

        # Cloudflare Turnstile, which keeps bots from sending the contact form.
        # Development uses the test keys unless real ones are set.
        self.TURNSTILE_SITE_KEY = os.environ.get('TURNSTILE_SITE_KEY', TURNSTILE_TEST_SITE_KEY)
        self.TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY', TURNSTILE_TEST_SECRET_KEY)


class DevSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

        self.ALLOWED_HOSTS = ['localhost', '127.0.0.1']
        self.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

        # Locally, each language gets its own loopback host name so the
        # domain-based language switching can be tested without editing
        # /etc/hosts: http://localhost:8000 (EN) and http://127.0.0.1:8000 (PT-BR).
        self.LANGUAGE_DOMAINS = {
            'en': 'localhost',
            'pt-br': '127.0.0.1',
        }

        # E-mails are printed in the terminal instead of being sent, unless
        # EMAIL_BACKEND is set
        self.EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


class DevDockerSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

        self.ALLOWED_HOSTS = ['localhost', '127.0.0.1']
        self.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': str(os.environ['DB_NAME']),
                'USER': str(os.environ['DB_USER']),
                'PASSWORD': str(os.environ['DB_PASSWORD']),
                'HOST': str(os.environ['DB_HOST']),
                'PORT': str(os.environ.get('DB_PORT', 5432)),
            }
        }
        self.LANGUAGE_DOMAINS = {
            'en': 'localhost',
            'pt-br': '127.0.0.1',
        }

        # E-mails are printed in the terminal instead of being sent, unless
        # EMAIL_BACKEND is set
        self.EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


class ServerSettings(BaseSettings):
    """What staging and production have in common (see deploy/README.md)."""

    def __init__(self) -> None:
        super().__init__()

        self.DATABASES = server_database()
        self.MEDIA_STORAGE = r2_media_storage()
        self.MEDIA_URL = f"https://{os.environ['MEDIA_DOMAIN']}/"
        self.HTTPS = True

        # Real Turnstile keys are required outside development
        self.TURNSTILE_SITE_KEY = str(os.environ['TURNSTILE_SITE_KEY'])
        self.TURNSTILE_SECRET_KEY = str(os.environ['TURNSTILE_SECRET_KEY'])


class StagingSettings(ServerSettings):

    def __init__(self) -> None:
        super().__init__()

        # The first one is the host the deploys check
        self.ALLOWED_HOSTS = [
            'staging.lavedonio.com',
            'staging.lavedonio.com.br',
        ]
        self.LANGUAGE_DOMAINS = {
            'en': 'staging.lavedonio.com',
            'pt-br': 'staging.lavedonio.com.br',
        }

        # Short, so a mistake on staging doesn't lock browsers out for long
        self.HSTS_SECONDS = 3600
        self.NOINDEX = True
        self.LOGIN_REQUIRED = True

        # The contact form's e-mails are only written to the server log, unless
        # EMAIL_BACKEND is set
        self.EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


class ProductionSettings(ServerSettings):

    def __init__(self) -> None:
        super().__init__()

        # The first one is the host the deploys check
        self.ALLOWED_HOSTS = [
            'lavedonio.com',
            'www.lavedonio.com',
            'lavedonio.com.br',
            'www.lavedonio.com.br',
        ]
        self.LANGUAGE_DOMAINS = {
            'en': 'lavedonio.com',
            'pt-br': 'lavedonio.com.br',
        }

        self.HSTS_SECONDS = 31536000


env_mapping = {
    'development': DevSettings,
    'docker_development': DevDockerSettings,
    'staging': StagingSettings,
    'production': ProductionSettings,
}

EnvironmentSettings = env_mapping[os.environ['ENVIRONMENT']]

environment_settings: BaseSettings = EnvironmentSettings()
