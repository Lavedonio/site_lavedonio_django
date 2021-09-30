"""
Django staging settings for site_lavedonio_django project.

Created based on 'django-admin startproject' command using Django 3.2.7.

Edited source folder from site_lavedonio_django to site_core.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from .config import config
from .base import *


# Setting environment name to escape unfinnished or testing pages
ENVIRONMENT = "staging"


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config["SECRET_KEY"]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (str(config.get("DEBUG_VALUE")) == "True")

ALLOWED_HOSTS = [
    'staging.lavedonio.com.br',         # .com.br domain
    'staging.lavedonio.com',            # .com domain
    'lavedonio-staging.herokuapp.com',  # Heroku app default domain
    '45.79.220.173'                     # Linode IP Address
]


# Custom Installed apps
INSTALLED_APPS += ['storages']


# Root location
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'


# E-mail configuration
DEFAULT_FROM_EMAIL = config.get("EMAIL_USER")
EMAIL_HOST_USER = config.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = config.get("EMAIL_PASS")


# RECAPTCHA settings
RECAPTCHA_PUBLIC_KEY = config["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = config["RECAPTCHA_PRIVATE_KEY"]

# Google Analytics
ANALYTICS_ID = config.get("ANALYTICS_ID")


# Storage settings
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = config.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = config.get("AWS_STORAGE_BUCKET_NAME")

AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_REGION_NAME = 'us-east-2'
S3_USE_SIGV4 = True


# Database settings
if config.get("SERVER_TYPE") == "heroku":
    # Heroku settings
    import django_heroku
    django_heroku.settings(locals())
else:
    # Database
    # https://docs.djangoproject.com/en/3.2/ref/settings/#databases

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config.get("DB_NAME"),
            'USER': config.get("DB_USER"),
            'PASSWORD': config.get("DB_PASS"),
            'HOST': "localhost",
            'PORT': "",
        }
    }


# Enforcing HTTPS traffic
if str(config.get("HTTPS_TRAFFIC_ONLY")) == "True":
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
