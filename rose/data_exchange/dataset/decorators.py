"""
Dataset-specific decorators
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Concatenate, ParamSpec, Protocol, TypeVar

    PR = ParamSpec("PR")
    T = TypeVar("T")

    class _Lockable(Protocol):
        @property
        def locked(self) -> bool: ...

    LockableT = TypeVar("LockableT", bound=_Lockable)


def check_locked(
    method: Callable[Concatenate[LockableT, PR], T],
) -> Callable[Concatenate[LockableT, PR], T]:
    """
    Guard mutating methods when the dataset metadata is locked
    """

    @functools.wraps(method)
    def wrapper(self: LockableT, /, *args: PR.args, **kwargs: PR.kwargs) -> T:
        if self.locked:
            raise RuntimeError("Object is locked and cannot be modified.")
        return method(self, *args, **kwargs)

    return wrapper
