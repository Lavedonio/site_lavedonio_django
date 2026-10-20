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


class BaseSettings:

    def __init__(self) -> None:
        self.BASE_DIR = BASE_DIR
        self.SECRET_KEY = str(os.environ['SECRET_KEY'])
        self.DEBUG = str(os.environ['DEBUG_VALUE']) == 'True'
        self.ALLOWED_HOSTS = []
        self.DATABASES = {}

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


class StagingSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

        self.ALLOWED_HOSTS = [
            'staging.lavedonio.com',
            'staging.lavedonio.com.br',
        ]
        self.LANGUAGE_DOMAINS = {
            'en': 'staging.lavedonio.com',
            'pt-br': 'staging.lavedonio.com.br',
        }

        # Real Turnstile keys are required outside development
        self.TURNSTILE_SITE_KEY = str(os.environ['TURNSTILE_SITE_KEY'])
        self.TURNSTILE_SECRET_KEY = str(os.environ['TURNSTILE_SECRET_KEY'])


class ProductionSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

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

        # Real Turnstile keys are required outside development
        self.TURNSTILE_SITE_KEY = str(os.environ['TURNSTILE_SITE_KEY'])
        self.TURNSTILE_SECRET_KEY = str(os.environ['TURNSTILE_SECRET_KEY'])


env_mapping = {
    'development': DevSettings,
    'docker_development': DevDockerSettings,
    'staging': StagingSettings,
    'production': ProductionSettings,
}

EnvironmentSettings = env_mapping[os.environ['ENVIRONMENT']]

environment_settings: BaseSettings = EnvironmentSettings()
