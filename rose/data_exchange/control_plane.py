"""Transport-neutral control-plane protocol for remote ROSE coordination."""

from __future__ import annotations

from typing import Protocol

from rose.data_exchange.descriptors import RoseDataDescriptor
from rose.data_exchange.models import (
    ClientConfig,
    ClientRegistration,
    DataEvent,
    SubscriptionRequest,
)


class ControlPlaneClient(Protocol):
    """Protocol for remote access to the ROSE coordinator process."""

    def register_client(self, registration: ClientRegistration) -> ClientConfig:
        """Register a remote client and receive runtime configuration."""

    def renew_registration(self, rose_client_id: str) -> ClientConfig:
        """Renew a client lease and refresh runtime configuration."""

    def register_descriptor(self, descriptor: RoseDataDescriptor) -> str:
        """Register a canonical descriptor and return its identifier."""

    def subscribe(self, request: SubscriptionRequest) -> None:
        """Register a remote subscription for descriptor events."""

    def fetch_events(self, subscriber_id: str, after_event_id: int = 0) -> list[DataEvent]:
        """Fetch queued events for a remote subscriber."""
