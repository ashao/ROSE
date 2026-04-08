"""
ROSE client manager skeleton for registration and configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from rose.data_exchange.client.models import ClientConfig, ClientRegistration


@dataclass
class RoseClientManager:
    """
    Registry/mediator that issues ROSE client identifiers and options
    """

    _registry: dict[str, ClientRegistration] = field(default_factory=dict)
    _counter: int = 0
    key_format: Optional[str] = "{app_name}:{rose_client_id}:{key}"

    def register_client(self, registration: ClientRegistration) -> ClientConfig:
        """
        Register a client and return a configuration container

        The ROSE client manager is responsible for issuing client identifiers and
        potentially setting up other configuration options including the location
        of the datastore and event stream backends.
        """
        self._counter += 1
        rose_client_id = f"rose-client-{self._counter}"
        self._registry[rose_client_id] = registration
        return ClientConfig(
            rose_client_id=rose_client_id,
            key_format=self.key_format,
            coordinator_endpoint="rose-control://main",
            datastore_endpoint="datastore://shared",
            event_stream_endpoint="rose-events://main",
            registration_ttl_s=300,
        )

    def get_registration(self, rose_client_id: str) -> ClientRegistration:
        """
        Return registration info for an already-registered client
        """
        return self._registry[rose_client_id]
