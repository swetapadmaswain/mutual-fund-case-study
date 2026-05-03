"""
Custom exceptions for the Mutual Fund FAQ Assistant.
"""


class MutualFundFAQException(Exception):
    """Base exception for the application."""
    pass


class DataCollectionError(MutualFundFAQException):
    """Raised when data collection fails."""
    pass


class SourceValidationError(MutualFundFAQException):
    """Raised when source validation fails."""
    pass


class ComplianceError(MutualFundFAQException):
    """Raised when compliance requirements are violated."""
    pass


class NetworkError(MutualFundFAQException):
    """Raised when network operations fail."""
    pass


class ParsingError(MutualFundFAQException):
    """Raised when content parsing fails."""
    pass


class ConfigurationError(MutualFundFAQException):
    """Raised when configuration is invalid."""
    pass


class CacheError(MutualFundFAQException):
    """Raised when cache operations fail."""
    pass
