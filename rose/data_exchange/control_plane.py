"""
Transport-neutral control-plane protocol for remote ROSE coordination
"""

from __future__ import annotations

from typing import Protocol

from rose.data_exchange.client.models import ClientConfig, ClientRegistration
from rose.data_exchange.data_manager.models import SubscriptionRequest
from rose.data_exchange.dataset import RoseDataDescriptor


class ControlPlaneClient(Protocol):
    """
    Protocol for remote access to the ROSE coordinator process
    """

    def register_client(self, registration: ClientRegistration) -> ClientConfig:
        """
        Register a remote client and receive runtime configuration
        """
        ...

    def register_outgoing_descriptor(self, descriptor: RoseDataDescriptor) -> str:
        """
        Register a canonical descriptor and return its identifier
        """
        ...

    def register_incoming_descriptor(self, descriptor: RoseDataDescriptor) -> str:
        """
        Register a canonical descriptor and return its identifier
        """
        ...

    def renew_registration(self, rose_client_id: str) -> ClientConfig:
        """
        Renew an existing client lease and return refreshed configuration
        """
        ...
