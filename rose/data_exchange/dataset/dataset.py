"""
Dataset container and metadata for data exchange operations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Union, TYPE_CHECKING

import numpy as np

from rose.data_exchange.dataset.decorators import check_locked

if TYPE_CHECKING:
    import numpy.typing as npt
    from typing_extensions import Self


class _MetadataMixin:
    """
    Mixin to add metadata handling to objects
    """

    metadata: dict[str, Any] = {}
    locked: bool = False

    @check_locked
    def add_metadata_with_key_value(self, key: str, value: Any) -> None:
        """
        Update metadata with a single key-value pair

        :param key: metadata key to add or update
        :param value: value to associate with the metadata key
        """
        self.metadata[key] = value

    @check_locked
    def add_metadata_with_dict(self, metadata_dict: dict[str, Any]) -> None:
        """
        Update metadata with multiple key-value pairs from a dictionary

        :param metadata_dict: dictionary of metadata key-value pairs to add or update
        """
        self.metadata.update(metadata_dict)

    @check_locked
    def remove_metadata_key(self, key: str) -> None:
        """
        Remove a metadata key if it exists

        :param key: metadata key to remove
        """
        self.metadata.pop(key, None)


class DescribedTensor(np.ndarray, _MetadataMixin):
    """
    Extension of numpy ndarray to include metadata for data exchange
    """

    def __new__(
        cls, input_array: npt.ArrayLike, metadata: dict[str, Any] | None = None
    ) -> Self:
        obj = np.asarray(input_array).view(cls)
        obj.metadata = metadata or {}
        return obj


@dataclass
class Dataset(_MetadataMixin):
    """
    Container holding one or more tensors and associated metadata
    """

    name: str
    tensors: dict[str, np.ndarray | DescribedTensor] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_tensor(
        self, field_name: str, tensor: Union[DescribedTensor, np.ndarray]
    ) -> None:
        """
        Add or replace a tensor field in the dataset
        """
        self.tensors[field_name] = tensor

    def get_tensor(self, field_name: str) -> DescribedTensor | np.ndarray:
        """
        Retrieve a tensor field by name
        """
        return self.tensors[field_name]

    def with_client_id(self, rose_client_id: str) -> "Dataset":
        """
        Inject the manager-issued client identifier into metadata
        """
        self.metadata["rose_client_id"] = rose_client_id
        return self
