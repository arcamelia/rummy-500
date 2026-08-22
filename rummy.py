"""Package-level convenience module for rummy utilities.

This module re-exports commonly used helpers so external code can:

    import rummy
    rummy.validate_snapshot(...)

"""
from validators import validate_snapshot

__all__ = ["validate_snapshot"]
