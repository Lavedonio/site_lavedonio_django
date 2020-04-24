"""
Django development settings for site_lavedonio_django project.

Created based on 'django-admin startproject' command using Django 2.2.10.

Edited source folder from site_lavedonio_django to site_core.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os
from .config import config
from .base import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'xgjs_fh170ta^c580g7#q!yp4r$7jcox@(^jva_)j!j9r!i_l8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# E-mail configuration
DEFAULT_FROM_EMAIL = config["EMAIL_USER"]
EMAIL_HOST_USER = config["EMAIL_USER"]
EMAIL_HOST_PASSWORD = config["EMAIL_PASS"]


# RECAPTCHA settings
RECAPTCHA_PUBLIC_KEY = config.get("RECAPTCHA_PUBLIC_KEY")
RECAPTCHA_PRIVATE_KEY = config.get("RECAPTCHA_PRIVATE_KEY")
