"""
Data manager skeleton for contract-aware event-driven dataset tracking
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from rose.data_exchange.data_manager.models import DataEvent, SourceSpec, SubscriptionRequest
from rose.data_exchange.dataset import Dataset
from rose.data_exchange.dataset import RoseDataDescriptor


@dataclass
class DatasetHandle:
    """
    Handle used to configure and observe dataset completeness
    """

    descriptor_id: str
    canonical_descriptor_id: str
    sources: dict[str, SourceSpec] = field(default_factory=dict)
    received_parts: dict[str, int] = field(default_factory=dict)

    def add_source(self, source: SourceSpec) -> None:
        """
        Add a source that contributes data to completeness accounting
        """
        self.sources[source.source_id] = source
        self.received_parts[source.source_id] = 0

    def mark_part_received(self, source_id: str) -> None:
        """
        Record that one source-part has been posted
        """
        self.received_parts[source_id] = self.received_parts.get(source_id, 0) + 1

    @property
    def is_complete(self) -> bool:
        """
        Return whether all declared sources have contributed expected parts
        """
        if not self.sources:
            return True
        for source_id, source in self.sources.items():
            if self.received_parts.get(source_id, 0) < source.expected_parts:
                return False
        return True


@dataclass
class DataManager:
    """
    Single source of truth for descriptor registration and dataset state
    """

    _descriptors: dict[str, RoseDataDescriptor] = field(default_factory=dict)
    _canonical_descriptor_ids: dict[str, str] = field(default_factory=dict)
    _handles: dict[str, DatasetHandle] = field(default_factory=dict)
    _datasets: dict[str, Dataset] = field(default_factory=dict)
    _events: list[DataEvent] = field(default_factory=list)
    _next_event_id: int = 1

    def register_descriptor(self, descriptor: RoseDataDescriptor) -> DatasetHandle:
        """
        Register canonical descriptor and return a handle usable by ROSE workflows to
        track completeness
        """
        existing_unique_id = self.resolve_descriptor_id(descriptor.descriptor_id)
        if existing_unique_id is not None:
            existing_descriptor = self._descriptors[existing_unique_id]
            # Manage case where the descriptor has already been registered. If the descriptors
            # differ, this is an error, otherwise simply return the previous registration handle.
            if existing_descriptor != descriptor:
                raise ValueError(
                    "Descriptor mismatch for canonical registration: "
                    f"{descriptor.descriptor_id}"
                )
            return self._handles[existing_unique_id]

        unique_descriptor_id = f"{descriptor.descriptor_id}:{uuid4().hex}"
        self._canonical_descriptor_ids[descriptor.descriptor_id] = unique_descriptor_id
        self._descriptors[unique_descriptor_id] = descriptor
        handle = DatasetHandle(
            descriptor_id=unique_descriptor_id,
            canonical_descriptor_id=descriptor.descriptor_id,
        )
        self._handles[unique_descriptor_id] = handle
        return handle

    def resolve_descriptor_id(self, descriptor_id: str) -> str | None:
        """
        Resolve a canonical descriptor id to its unique registered descriptor id
        """
        return self._canonical_descriptor_ids.get(descriptor_id)

    def get_descriptor(self, unique_descriptor_id: str) -> RoseDataDescriptor | None:
        """
        Retrieve a registered canonical descriptor by its unique id
        """
        return self._descriptors.get(unique_descriptor_id)

    def post_dataset(
        self,
        descriptor_id: str,
        dataset: Dataset,
        source_id: str | None = None,
    ) -> None:
        """
        Store a dataset update and record an event for remote subscribers
        """
        self._datasets[descriptor_id] = dataset
        handle = self._handles.get(descriptor_id)
        if handle and source_id is not None:
            handle.mark_part_received(source_id)

        event = DataEvent(
            event_id=self._next_event_id,
            descriptor_id=descriptor_id,
            dataset_name=dataset.name,
            source_id=source_id,
            is_complete=handle.is_complete if handle else True,
            metadata=dataset.metadata.copy(),
        )
        self._events.append(event)
        self._next_event_id += 1

    def get_dataset(self, descriptor_id: str) -> Dataset | None:
        """
        Retrieve latest dataset for a descriptor id
        """
        return self._datasets.get(descriptor_id)
