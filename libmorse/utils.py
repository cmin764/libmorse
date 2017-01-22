"""Various frequently used common utilities."""


import logging
import os

import mock

from libmorse import exceptions
from libmorse import settings


def get_logger(name, debug=settings.DEBUG, use_logging=settings.LOGGING):
    """Obtain a logger object given a name."""
    if not use_logging:
        return mock.Mock()
    logging.basicConfig(
        filename=settings.LOGFILE,
        format="%(levelname)s - %(asctime)s - %(message)s"
    )
    log = logging.getLogger(name)
    level = logging.DEBUG if debug else logging.INFO
    log.setLevel(level)
    return log


def get_return_code(exc):
    """Get a return code based on the raised exception."""
    if not exc:
        return 0             # all good, clean code
    if isinstance(exc, exceptions.MorseError):
        return exc.CODE      # known error, known code
    return exceptions.MorseError.CODE    # normalize to default error code


def get_res(name):
    """Get resource path based on file name."""
    return os.path.join(settings.PROJECT, "res", name)


def get_res_content(name):
    """Get resource content based on file name."""
    with open(get_res(name), "r") as stream:
        return stream.read()


def get_mor_code(data):
    """Get MOR code given `data`."""
    if not data:
        return []

    mor_code = []
    for line in data.splitlines():
        # Remove extra spaces and get rig of comments.
        line = line.strip()
        idx = line.find("#")
        if idx != -1:
            line = line[:idx].strip()
        if not line:
            continue
        # Now get the status and time length of the quanta.
        chunks = line.split()
        state, duration = bool(int(chunks[0])), float(chunks[1])
        mor_code.append((state, duration))
    return mor_code
