"""Dataset container and metadata for data exchange operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class Dataset:
    """Container holding one or more tensors and associated metadata."""

    name: str
    tensors: dict[str, np.ndarray] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_tensor(self, field_name: str, tensor: np.ndarray) -> None:
        """Add or replace a tensor field in the dataset."""
        self.tensors[field_name] = tensor

    def with_client_id(self, rose_client_id: str) -> "Dataset":
        """Inject the manager-issued client identifier into metadata."""
        self.metadata["rose_client_id"] = rose_client_id
        return self
