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


class StagingSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

        self.ALLOWED_HOSTS = [
            'staging.lavedonio.com',
            'staging.lavedonio.com.br',
        ]


class ProductionSettings(BaseSettings):

    def __init__(self) -> None:
        super().__init__()

        self.ALLOWED_HOSTS = [
            'lavedonio.com',
            'www.lavedonio.com',
            'lavedonio.com.br',
            'www.lavedonio.com.br',
        ]


env_mapping = {
    'development': DevSettings,
    'docker_development': DevDockerSettings,
    'staging': StagingSettings,
    'production': ProductionSettings,
}

EnvironmentSettings = env_mapping[os.environ['ENVIRONMENT']]

environment_settings: BaseSettings = EnvironmentSettings()
