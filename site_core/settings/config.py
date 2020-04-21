import os


try:
    from .secrets import secrets
    config = secrets
except ModuleNotFoundError:

    config = {}

    config["ENVIRONMENT"] = os.environ.get("ENVIRONMENT")
    config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    config["DEBUG_VALUE"] = os.environ.get("DEBUG_VALUE")
    config["DB_NAME"] = os.environ.get("DB_NAME")
    config["DB_USER"] = os.environ.get("DB_USER")
    config["DB_PASS"] = os.environ.get("DB_PASS")
    config["RECAPTCHA_PUBLIC_KEY"] = os.environ.get("RECAPTCHA_PUBLIC_KEY")
    config["RECAPTCHA_PRIVATE_KEY"] = os.environ.get("RECAPTCHA_PRIVATE_KEY")
    config["EMAIL_USER"] = os.environ.get("EMAIL_USER")
    config["EMAIL_PASS"] = os.environ.get("EMAIL_PASS")
    config["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    config["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    config["AWS_STORAGE_BUCKET_NAME"] = os.environ.get("AWS_STORAGE_BUCKET_NAME")

    if config["ENVIRONMENT"] is None:
        config["ENVIRONMENT"] = "development"
