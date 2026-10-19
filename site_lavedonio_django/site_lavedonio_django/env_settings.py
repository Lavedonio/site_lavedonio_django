"""
This file contains environment-specific settings configurations, in order to
isolate them from the default Django settings.py file.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / '.env')


class BaseSettings:

    def __init__(self) -> None:
        self.BASE_DIR = BASE_DIR
        self.SECRET_KEY = str(os.environ['SECRET_KEY'])
        self.DEBUG = str(os.environ['DEBUG_VALUE']) == 'True'
        self.ALLOWED_HOSTS = []
        self.DATABASES = {}

        # Which host serves each language ("www." prefixes are ignored).
        # Requests to any other host are served in LANGUAGE_CODE.
        self.LANGUAGE_DOMAINS = {}

        # Google Analytics measurement ID (optional). It's only loaded for
        # visitors who allow cookies.
        self.ANALYTICS_ID = os.environ.get('ANALYTICS_ID') or None


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


env_mapping = {
    'development': DevSettings,
    'docker_development': DevDockerSettings,
    'staging': StagingSettings,
    'production': ProductionSettings,
}

EnvironmentSettings = env_mapping[os.environ['ENVIRONMENT']]

environment_settings: BaseSettings = EnvironmentSettings()
