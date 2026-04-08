"""
Descriptor validation policies and validator types
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rose.data_exchange.dataset.descriptor import RoseDataDescriptor


@dataclass(frozen=True)
class ValidationPolicy:
    """
    Validation controls for descriptor field and cross-field checks
    """

    fail_if_missing: bool = False
    warn_if_missing: bool = True
    fail_if_mismatch: bool = False
    warn_if_mismatch: bool = True
    fail_if_extra: bool = False
    warn_if_extra: bool = True


@dataclass
class DataDescriptorValidator:
    """
    Validator that compares app descriptors against canonical ROSE descriptors
    """

    default_policy: ValidationPolicy = field(default_factory=ValidationPolicy)

    def validate(
        self,
        canonical: RoseDataDescriptor,
        app_descriptor: RoseDataDescriptor,
    ) -> bool:
        """
        Validate descriptor compatibility and return warning messages
        """
        return canonical == app_descriptor
