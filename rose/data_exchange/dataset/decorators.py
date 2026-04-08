"""
Dataset-specific decorators
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def check_locked(method: Callable[..., Any]) -> Callable[..., Any]:
    """
    Guard mutating methods when the dataset metadata is locked
    """

    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if getattr(self, "locked", False):
            raise RuntimeError("Object is locked and cannot be modified.")
        return method(self, *args, **kwargs)

    return wrapper
