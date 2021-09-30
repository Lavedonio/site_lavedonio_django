import os
from dotenv import load_dotenv
from .base import BASE_DIR


load_dotenv(BASE_DIR / '.env')

config = {}

env_vars = [
    "ENVIRONMENT",
    "SECRET_KEY",
    "DEBUG_VALUE",
    "SERVER_TYPE",
    "DB_NAME",
    "DB_USER",
    "DB_PASS",
    "RECAPTCHA_PUBLIC_KEY",
    "RECAPTCHA_PRIVATE_KEY",
    "EMAIL_USER",
    "EMAIL_PASS",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_STORAGE_BUCKET_NAME",
    "HTTPS_TRAFFIC_ONLY",
    "ANALYTICS_ID"
]

for var in env_vars:
    config[var] = os.environ.get(var)

if config["ENVIRONMENT"] is None:
    config["ENVIRONMENT"] = "development"
