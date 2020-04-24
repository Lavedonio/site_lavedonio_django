# Imports the configuration file. If nothing is set, defaults to the development settings.
from .config import config

# Imports the correct settings according to the environment
if config["ENVIRONMENT"] == "production":
    from .production import *

elif config["ENVIRONMENT"] == "staging":
    from .staging import *

else:
    from .development import *
