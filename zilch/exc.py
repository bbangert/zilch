"""zilch exceptions"""
class ZilchException(BaseException):
    """Base Zilch Exception Class"""


class ConfigurationError(ZilchException):
    """Configuration not setup properly"""
