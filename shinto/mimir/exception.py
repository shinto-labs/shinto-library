"""Exceptions for Mimir."""

from shinto.exceptions import ShintoWarning, ShintoException

class MimirException(ShintoException):
    """Exception for Mimir."""

class MimirWarning(ShintoWarning):
    """Warning for Mimir."""

class MimirEntityException(MimirException):
    """Exception for entity operations."""

class MimirEntityNotFoundException(MimirEntityException):
    """Exception for entity not found."""

class MimirEntityAlreadyExistsException(MimirEntityException):
    """Exception for entity already exists."""

class MimirEntityInvalidException(MimirEntityException):
    """Exception for entity invalid."""

class MimirEntityValidationError(MimirEntityException):
    """Exception for entity validation error."""
