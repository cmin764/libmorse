"""Various settings and configuration used by the entire project."""


import os


# Project directory (package parent).
PROJECT = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__),
        os.path.pardir
    )
)
ETC = os.path.join(PROJECT, "etc", "libmorse")
RESOURCE = os.path.join(PROJECT, "res", "libmorse")

# Log information.
LOGGING = True
# Show debugging/verbose info.
DEBUG = False
# Logging file.
LOGFILE = "libmorse.log"

# Misc.
ENCODING = "utf-8"
