########################################################
#                                                      #
#           Place sensitive information here           #
#                                                      #
# ATTENTION: don't edit this file. Copy and rename it  #
#            to 'secrets.py' to set the configuration. #
#                                                      #
########################################################


secrets = {
    #Django
    "ENVIRONMENT": "development",
    "SECRET_KEY": "",
    "DEBUG_VALUE": "True",
    "SERVER_TYPE": "",
    "HTTPS_TRAFFIC_ONLY": "",

    # E-mail
    "EMAIL_USER": "",
    "EMAIL_PASS": "",

    # RECAPTCHA
    "RECAPTCHA_PUBLIC_KEY": "",
    "RECAPTCHA_PRIVATE_KEY": "",

    # Postgres Database
    "DB_NAME": "",
    "DB_USER": "",
    "DB_PASS": "",

    # AWS
    "AWS_ACCESS_KEY_ID": "",
    "AWS_SECRET_ACCESS_KEY": "",
    "AWS_STORAGE_BUCKET_NAME": "",

    # Google Analytics
    "ANALYTICS_ID": ""
}
