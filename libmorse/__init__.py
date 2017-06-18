"""Main package classes, functions and utilities."""


from .exceptions import ProcessMorseError
from .settings import PROJECT
from .utils import (
    get_logger,
    get_mor_code,
    get_resource,
    get_return_code,
)
