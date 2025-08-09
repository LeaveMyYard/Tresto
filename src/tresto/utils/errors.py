class TrestoError(Exception):
    """Base class for all Tresto errors."""


class InitError(TrestoError):
    """Raised when there is an error during initialization."""
