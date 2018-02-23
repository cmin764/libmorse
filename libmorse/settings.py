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

# Translator settings.
# Minimum and maximum size of the analysed active range of morse signals.
SIGNAL_RANGE = (12, 36)
# Minimal accepted delta between any two means in percentage of unit.
MEAN_MIN_DIFF = 1.1
# Usual unit length in milliseconds.
UNIT = 300.0    # should be float
