"""Core data models used by the data exchange skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ClientRegistration:
    """Metadata emitted by a client when registering with the manager."""

    local_client_id: str
    app_name: str
    rank: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClientConfig:
    """Configuration returned by the client manager after registration."""

    rose_client_id: str
    enabled_fields: tuple[str, ...] = ()
    key_format: str | None = None
    coordinator_endpoint: str | None = None
    datastore_endpoint: str | None = None
    event_stream_endpoint: str | None = None
    workflow_id: str | None = None
    registration_ttl_s: int | None = None
    extra_options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceSpec:
    """Definition of a source that contributes to a dataset's completeness."""

    source_id: str
    expected_parts: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubscriptionRequest:
    """Remote subscription request for descriptor-scoped data events."""

    subscriber_id: str
    descriptor_id: str
    transport: str
    target: str | None = None
    start_event_id: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DataEvent:
    """Transport-neutral event emitted when dataset state changes."""

    event_id: int
    descriptor_id: str
    dataset_name: str
    source_id: str | None = None
    is_complete: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
