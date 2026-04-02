"""Client APIs for generic and ROSE-driven workflows."""

from __future__ import annotations

from concurrent.futures import Future
from typing import Any

from rose.data_exchange.backend import DataBackend
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.dataset import Dataset
from rose.data_exchange.models import ClientConfig, ClientRegistration


class BasicClient:
    """Minimal put/get client usable outside of ROSE-managed workflows."""

    def __init__(self, backend: DataBackend, base_key_format: str = "{key}") -> None:
        self._backend = backend
        self._base_key_format = base_key_format
        self._config: ClientConfig | None = None

    def initialize(self) -> None:
        """Connect to backend and freeze immutable runtime behavior."""
        self._backend.connect()

    def apply_manager_response(self, config: ClientConfig | None) -> None:
        """Accept only stateless/no-op manager responses for BasicClient."""
        if config and config.extra_options:
            raise ValueError("BasicClient does not accept stateful manager responses")
        self._config = config

    def put_async(self, key: str, dataset: Dataset) -> Future[None]:
        """Asynchronously put a dataset."""
        return self._backend.put_dataset(self.build_key(key), dataset)

    def get_future(self, key: str) -> Future[Dataset]:
        """Retrieve a dataset as a future for latency hiding."""
        return self._backend.get_dataset(self.build_key(key))

    def get_blocking(self, key: str, timeout: float | None = None) -> Dataset:
        """Retrieve a dataset and block until available or timeout."""
        return self.get_future(key).result(timeout=timeout)

    def close(self) -> None:
        """Close any backend resources."""
        self._backend.close()

    def build_key(self, key: str, **components: Any) -> str:
        """Construct a backend key locally from the configured key format."""
        return self._resolve_key_format().format(key=key, **components)

    def _resolve_key_format(self) -> str:
        """Return the effective key format for this client."""
        return self._base_key_format


class AdvancedClient(BasicClient):
    """ROSE-driven client supporting manager-guided key and data behavior."""

    def __init__(self, backend: DataBackend, base_key_format: str = "{key}") -> None:
        super().__init__(backend=backend, base_key_format=base_key_format)
        self._rose_client_id: str | None = None
        self._registration: ClientRegistration | None = None
        self._control_plane: ControlPlaneClient | None = None

    def register(
        self,
        registration: ClientRegistration,
        control_plane: ControlPlaneClient,
    ) -> ClientConfig:
        """Register with the remote ROSE control plane and apply config."""
        self._registration = registration
        self._control_plane = control_plane
        config = control_plane.register_client(registration)
        self.apply_manager_response(config)
        return config

    def renew_registration(self) -> ClientConfig:
        """Renew the client lease with the remote control plane."""
        if self._control_plane is None or self._rose_client_id is None:
            raise ValueError("AdvancedClient must be registered before renewal")
        config = self._control_plane.renew_registration(self._rose_client_id)
        self.apply_manager_response(config)
        return config

    def apply_manager_response(self, config: ClientConfig | None) -> None:
        """Accept and store stateful response from manager for AdvancedClient."""
        if config is None:
            raise ValueError("AdvancedClient requires a manager response")
        self._config = config
        self._rose_client_id = config.rose_client_id

    def put_async(self, key: str, dataset: Dataset) -> Future[None]:
        """Inject manager-issued client id into metadata before upload."""
        if self._rose_client_id:
            dataset = dataset.with_client_id(self._rose_client_id)
        return super().put_async(key=key, dataset=dataset)

    def build_key(self, key: str, **components: Any) -> str:
        """Construct a key locally using manager-provided formatting rules."""
        if self._registration is None:
            return super().build_key(key, **components)

        context = {
            "app_name": self._registration.app_name,
            "key": key,
            "local_client_id": self._registration.local_client_id,
            "rank": self._registration.rank,
            "rose_client_id": self._rose_client_id,
        }
        context.update(self._registration.metadata)
        context.update(components)
        return self._resolve_key_format().format(**context)

    def _resolve_key_format(self) -> str:
        """Return the manager-supplied key format when available."""
        if self._config and self._config.key_format:
            return self._config.key_format
        return super()._resolve_key_format()
