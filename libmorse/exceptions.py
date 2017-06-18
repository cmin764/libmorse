"""Custom exceptions module for error code return ability."""


class MorseError(Exception):
    """Base exception class for all particular and derived errors."""

    CODE = 1    # generic code used for unhandled thrown exceptions


class ProcessMorseError(MorseError):
    """Generic exception for any aspect of a processing class/function."""

    CODE = 11
