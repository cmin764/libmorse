"""Main package classes, functions and utilities."""


from .exceptions import (
    MorseError,
    ProcessMorseError,
    TranslatorMorseError,
)
from .settings import PROJECT, UNIT
from .translator import (
    AlphabetTranslator,
    MorseTranslator,
    translate_morse,
)
from .utils import (
    get_logger,
    get_mor_code,
    get_return_code,
)


CLOSE_SENTINEL = MorseTranslator.CLOSE_SENTINEL
