"""Various settings and configuration used by the entire project."""


import os


# Project directory (package parent).
PROJECT = os.path.normpath(
    os.path.join(
        __file__,
        os.path.pardir,
        os.path.pardir
    )
)

# Log information.
LOGGING = True
# Show debugging/verbose info.
DEBUG = False
# Logging file.
LOGFILE = "libmorse.log"

ENCODING = "utf-8"
