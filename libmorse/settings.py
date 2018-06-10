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
# Minimal and maximal accepted delta between any two means in percentage of
# unit.
MEAN_MIN_DIFF = 1.1
MEAN_MAX_DIFF = 11.9
# Usual unit length in milliseconds.
UNIT = 300.0    # should be float
# Less than this from unit is considered undesired noise.
NOISE_RATIO = 0.1
# Enable translator renewal after certain states/events.
ENABLE_RENEWAL = False
# How many k-means iterations to run at most (getting non-empty clusters).
CLUSTER_ITER = 10
