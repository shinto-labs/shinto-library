"""Exceptions for Shinto."""


class ShintoException(Exception):
    """Base exception for Shinto."""


class ShintoWarning(Warning):
    """Base warning for Shinto."""


class ShintoSizeLimitException(ShintoException):
    """Exception raised when a size limit is exceeded."""


class ShintoNotFoundException(ShintoException):
    """Exception raised when a requested resource is not found."""


class ShintoBadInputException(ShintoException):
    """Exception raised for bad input."""
