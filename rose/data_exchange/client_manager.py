"""ROSE client manager skeleton for registration and configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from rose.data_exchange.models import ClientConfig, ClientRegistration


@dataclass
class RoseClientManager:
    """Registry/mediator that issues ROSE client identifiers and options."""

    _registry: dict[str, ClientRegistration] = field(default_factory=dict)
    _counter: int = 0

    def register_client(self, registration: ClientRegistration) -> ClientConfig:
        """Register a client and return workflow-specific configuration.

        The client manager defines the key format, but the client remains
        responsible for constructing the final backend key locally.
        """
        self._counter += 1
        rose_client_id = f"rose-client-{self._counter}"
        self._registry[rose_client_id] = registration
        return ClientConfig(
            rose_client_id=rose_client_id,
            key_format="{app_name}:{rose_client_id}:{key}",
            coordinator_endpoint="rose-control://main",
            datastore_endpoint="datastore://shared",
            event_stream_endpoint="rose-events://main",
            registration_ttl_s=300,
        )

    def get_registration(self, rose_client_id: str) -> ClientRegistration:
        """Return registration info for an already-registered client."""
        return self._registry[rose_client_id]
