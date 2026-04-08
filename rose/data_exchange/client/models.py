"""
Client-side data models used by data exchange clients and managers
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class ClientRegistration:
    """
    Metadata emitted by a client when registering with the manager
    """

    local_client_id: str
    app_name: str
    rank: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ClientConfig:
    """
    Configuration returned by the client manager after registration
    """

    rose_client_id: str
    enabled_fields: tuple[str, ...] = ()
    key_format: str | None = None
    coordinator_endpoint: str | None = None
    datastore_endpoint: str | None = None
    workflow_id: str | None = None
    extra_options: dict[str, Any] = field(default_factory=dict)


class DataIntent(str, Enum):
    """
    Declared direction of a dataset registered by an AdvancedClient
    """

    OUTGOING = "outgoing"
    INCOMING = "incoming"
    TWOWAY = "twoway"


@dataclass(frozen=True)
class ClientDatasetHandle:
    """
    Client-side handle returned when registering a dataset with the AdvancedClient

    Contains all necessary information needed to retrieve the requested dataset
    and validate the correct behaviour. This can be the key itself and intention.
    In general, this serves to provide one layer of obscurity such that the user
    is discouraged from using keys directly.
    """

    descriptor_id: str
    intent: DataIntent
    key: str
