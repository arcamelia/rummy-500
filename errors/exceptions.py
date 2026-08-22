"""Custom exception types for the rummy-500 project.

These allow callers to distinguish failure modes while remaining backwards
compatible with existing `ValueError`-based tests and code (several
exceptions subclass `ValueError`).
"""

class GameError(Exception):
    """Base class for game-related errors."""
    pass


class DeserializationError(ValueError, GameError):
    """Raised when deserializing malformed or invalid state."""
    pass


class IllegalMoveError(ValueError, GameError):
    """Raised when a requested move is illegal according to game rules."""
    pass


class GameStateError(ValueError, GameError):
    """Raised when the game state is inconsistent or invalid."""
    pass


class DuplicateIDError(DeserializationError):
    """Raised when duplicate `card_id` values are detected during deserialization."""
    pass
