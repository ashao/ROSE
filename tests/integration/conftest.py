from __future__ import annotations

from concurrent.futures import Future
from dataclasses import dataclass, field
import hashlib
import json

import pytest

from rose.data_exchange.client import AdvancedClient
from rose.data_exchange.client.models import ClientConfig, ClientRegistration
from rose.data_exchange.client_manager import RoseClientManager
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.data_manager import DataManager
from rose.data_exchange.dataset import Dataset, RoseDataDescriptor


@dataclass
class InMemoryBackend:
    """
    In-memory backend that forwards writes into the data manager
    """

    data_manager: DataManager
    storage: dict[str, Dataset] = field(default_factory=dict)

    def _descriptor_storage_key(self, descriptor_id: str) -> str:
        """
        Build a stable storage key by hashing the full descriptor payload
        """
        descriptor = self.data_manager.get_descriptor(descriptor_id)
        if descriptor is None:
            raise KeyError(f"Unknown descriptor id: {descriptor_id}")
        descriptor_payload = {
            "descriptor_id": descriptor.descriptor_id,
            "datafields": descriptor.datafields,
            "metadata": descriptor.metadata,
            "append_axis": descriptor.append_axis,
            "modification_policy": descriptor.modification_policy.value,
        }
        serialized = json.dumps(descriptor_payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def connect(self) -> None:
        """
        Connect backend
        """
        return None

    def put_dataset(self, key: str, dataset: Dataset) -> Future[None]:
        """
        Store dataset using a hash of the descriptor payload
        """
        descriptor_id = key
        storage_key = self._descriptor_storage_key(descriptor_id)
        self.storage[storage_key] = dataset
        source_id = dataset.metadata.get("rose_client_id")
        self.data_manager.post_dataset(descriptor_id, dataset, source_id=source_id)
        future: Future[None] = Future()
        future.set_result(None)
        return future

    def get_dataset(self, key: str) -> Future[Dataset]:
        """
        Retrieve dataset using a hash of the descriptor payload
        """
        descriptor_id = key
        storage_key = self._descriptor_storage_key(descriptor_id)
        future: Future[Dataset] = Future()
        future.set_result(self.storage[storage_key])
        return future

    def close(self) -> None:
        """
        Close backend
        """
        return None


@dataclass
class ClientControlPlane(ControlPlaneClient):
    """
    In-memory test control plane wiring manager and data manager together
    """

    client_manager: RoseClientManager
    data_manager: DataManager
    _configs: dict[str, ClientConfig] = field(default_factory=dict)

    def register_client(self, registration: ClientRegistration) -> ClientConfig:
        """
        Register client through the client manager
        """
        config = self.client_manager.register_client(registration)
        self._configs[config.rose_client_id] = config
        return config

    def register_outgoing_descriptor(self, descriptor: RoseDataDescriptor) -> str:
        """
        Register outgoing descriptor in data manager
        """
        unique_descriptor_id = self.data_manager.resolve_descriptor_id(
            descriptor.descriptor_id
        )
        if unique_descriptor_id is None:
            raise ValueError(
                "No canonical descriptor registered for outgoing descriptor_id: "
                f"{descriptor.descriptor_id}"
            )
        canonical_descriptor = self.data_manager.get_descriptor(unique_descriptor_id)
        if canonical_descriptor is None:
            raise ValueError(
                f"Canonical descriptor lookup failed: {descriptor.descriptor_id}"
            )
        if canonical_descriptor != descriptor:
            raise ValueError(
                f"Descriptor mismatch for canonical registration: {descriptor.descriptor_id}"
            )
        return unique_descriptor_id

    def register_incoming_descriptor(self, descriptor: RoseDataDescriptor) -> str:
        """
        Register incoming descriptor in data manager
        """
        unique_descriptor_id = self.data_manager.resolve_descriptor_id(
            descriptor.descriptor_id
        )
        if unique_descriptor_id is None:
            raise ValueError(
                "No canonical descriptor registered for incoming descriptor_id: "
                f"{descriptor.descriptor_id}"
            )
        canonical_descriptor = self.data_manager.get_descriptor(unique_descriptor_id)
        if canonical_descriptor is None:
            raise ValueError(
                f"Canonical descriptor lookup failed: {descriptor.descriptor_id}"
            )
        if canonical_descriptor != descriptor:
            raise ValueError(
                f"Descriptor mismatch for canonical registration: {descriptor.descriptor_id}"
            )
        return unique_descriptor_id

    def renew_registration(self, rose_client_id: str) -> ClientConfig:
        """
        Return latest known registration config
        """
        return self._configs[rose_client_id]


@pytest.fixture
def client_manager() -> RoseClientManager:
    """
    Fixture creating a client manager for tests
    """
    return RoseClientManager(key_format="{key}")


@pytest.fixture
def data_manager() -> DataManager:
    """
    Fixture creating a data manager for tests
    """
    return DataManager()


@pytest.fixture
def client_control_plane(
    client_manager: RoseClientManager,
    data_manager: DataManager,
) -> ClientControlPlane:
    """
    Fixture creating a basic control plane for tests
    """
    return ClientControlPlane(client_manager=client_manager, data_manager=data_manager)


@pytest.fixture
def backend(data_manager: DataManager) -> InMemoryBackend:
    """
    Fixture creating an in-memory backend for tests
    """
    return InMemoryBackend(data_manager=data_manager)


@pytest.fixture
def client1(
    backend: InMemoryBackend,
    client_control_plane: ClientControlPlane,
) -> AdvancedClient:
    """
    Fixture creating and registering an advanced client for tests
    """
    client = AdvancedClient(backend=backend)
    client.initialize()
    client.register(
        ClientRegistration(local_client_id="0", app_name="producer", rank=0),
        client_control_plane,
    )
    return client

@pytest.fixture
def client2(
    backend: InMemoryBackend,
    client_control_plane: ClientControlPlane,
) -> AdvancedClient:
    """
    Fixture creating and registering an advanced client for tests
    """
    client = AdvancedClient(backend=backend)
    client.initialize()
    client.register(
        ClientRegistration(local_client_id="1", app_name="consumer", rank=0),
        client_control_plane,
    )
    return client