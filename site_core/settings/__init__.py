# Tries to import configuration file. If it fails (probably because it doesn't exist),
# it defaults to the development settings.

try:
	from .config import config
except ModuleNotFoundError:
	config = {"ENVIRONMENT": "development"}

# Imports base settings and environment specific settings
from .base import *

if config["ENVIRONMENT"] == "development":
	from .development import *
else:
	from .staging import *
