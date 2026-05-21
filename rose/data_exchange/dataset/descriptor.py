"""
Descriptor definitions for ROSE data contracts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModificationPolicy(str, Enum):
    """
    Allowed mutation policies for datasets
    """

    OVERWRITE = "overwrite"
    APPEND_ONLY = "append-only"
    FIXED = "fixed"


@dataclass(frozen=True)
class RoseDataDescriptor:
    """
    Canonical ROSE descriptor governing workflow data contracts
    """

    descriptor_id: str
    datafields: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    append_axis: int | None = None
    modification_policy: ModificationPolicy = ModificationPolicy.OVERWRITE

    def __eq__(self, other: object) -> bool:
        """
        Equality check ignoring non-essential metadata fields
        """
        if not isinstance(other, RoseDataDescriptor):
            return NotImplemented
        return (
            self.descriptor_id == other.descriptor_id
            and self.datafields == other.datafields
            and self.append_axis == other.append_axis
            and self.modification_policy == other.modification_policy
        )
