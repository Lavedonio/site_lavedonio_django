# Imports the configuration file. If nothing is set, defaults to the development settings.
from .config import config

# Imports base settings and environment specific settings
from .base import *

if config["ENVIRONMENT"] == "staging":
    from .staging import *
else:
    from .development import *
