"""Data descriptors and validator skeletons for ROSE data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModificationPolicy(str, Enum):
    """Allowed mutation policies for datasets."""

    OVERWRITE = "overwrite"
    APPEND_ONLY = "append-only"
    FIXED = "fixed"


@dataclass(frozen=True)
class ValidationPolicy:
    """Validation controls for descriptor field and cross-field checks."""

    fail_if_missing: bool = False
    warn_if_missing: bool = True
    fail_if_mismatch: bool = False
    warn_if_mismatch: bool = True
    fail_if_extra: bool = False
    warn_if_extra: bool = True


@dataclass(frozen=True)
class DescriptorField:
    """A single required/optional data field and expected metadata."""

    name: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppDataDescriptor:
    """Application-declared descriptor used for local capability declaration."""

    fields: tuple[DescriptorField, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RoseDataDescriptor:
    """Canonical ROSE descriptor governing workflow data contracts."""

    descriptor_id: str
    fields: tuple[DescriptorField, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    validation_policy: ValidationPolicy = field(default_factory=ValidationPolicy)
    modification_policy: ModificationPolicy = ModificationPolicy.OVERWRITE
    append_axis: int | None = None


@dataclass
class DataDescriptorValidator:
    """Validator that compares app descriptors against canonical ROSE descriptors."""

    default_policy: ValidationPolicy = field(default_factory=ValidationPolicy)

    def validate(
        self,
        canonical: RoseDataDescriptor,
        app_descriptor: AppDataDescriptor,
    ) -> list[str]:
        """Validate descriptor compatibility and return warning messages."""
        warnings: list[str] = []
        # Skeleton only. Full implementation should enforce missing/mismatch/extra rules.
        if not canonical.fields:
            warnings.append("Canonical descriptor contains no fields")
        if not app_descriptor.fields:
            warnings.append("Application descriptor contains no fields")
        return warnings
