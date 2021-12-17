"""
Django development settings for site_lavedonio_django project.

Created based on 'django-admin startproject' command using Django 3.2.10.

Edited source folder from site_lavedonio_django to site_core.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from .config import config
from .base import *


# Setting environment name to escape unfinnished or testing pages
ENVIRONMENT = "development"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xgjs_fh170ta^c580g7#q!yp4r$7jcox@(^jva_)j!j9r!i_l8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Root location
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'


# E-mail configuration
DEFAULT_FROM_EMAIL = config.get("EMAIL_USER")
EMAIL_HOST_USER = config.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = config.get("EMAIL_PASS")


# RECAPTCHA settings
RECAPTCHA_PUBLIC_KEY = config.get("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = config.get("RECAPTCHA_PRIVATE_KEY")

# Google Analytics
ANALYTICS_ID = None  # Set to None in development
