# Imports the configuration file. If nothing is set, defaults to the development settings.

from .config import config

# Imports base settings and environment specific settings
from .base import *

if config["ENVIRONMENT"] == "development":
    from .development import *
else:
    from .staging import *
