"""Custom exception types for the rummy package."""
class GameError(Exception):
    pass


class DeserializationError(ValueError, GameError):
    pass


class IllegalMoveError(ValueError, GameError):
    pass


class GameStateError(ValueError, GameError):
    pass


class DuplicateIDError(DeserializationError):
    pass
