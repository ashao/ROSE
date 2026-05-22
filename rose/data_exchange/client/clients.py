"""
Client APIs for generic and ROSE-driven workflows
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from functools import wraps
from typing import Any, TYPE_CHECKING

from rose.data_exchange.backend import DataBackend
from rose.data_exchange.client.models import (
    ClientConfig,
    ClientDatasetHandle,
    ClientRegistration,
    DataIntent,
)
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.dataset import Dataset
from rose.data_exchange.dataset import RoseDataDescriptor

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec, TypeVar

    PR = ParamSpec("PR")
    T = TypeVar("T")
    AdvancedClientT = TypeVar("AdvancedClientT", bound="AdvancedClient")


def _require_registered(
    method: Callable[Concatenate[AdvancedClientT, PR], T],
) -> Callable[Concatenate[AdvancedClientT, PR], T]:
    """
    Ensure AdvancedClient registration is completed before method execution
    """

    @wraps(method)
    def wrapper(self: AdvancedClientT, /, *args: PR.args, **kwargs: PR.kwargs) -> T:
        if self._control_plane is None or self._rose_client_id is None:
            raise ValueError(
                "AdvancedClient must be registered before declaring dataset intents"
            )
        return method(self, *args, **kwargs)

    return wrapper


class BasicClient:
    """
    Minimal client usable outside of ROSE-managed workflows
    """

    def __init__(self, backend: DataBackend, base_key_format: str = "{key}") -> None:
        self._backend = backend
        self._base_key_format = base_key_format
        self._config: ClientConfig | None = None
        self._dataset_handles: dict[str, ClientDatasetHandle] = {}

    def initialize(self) -> None:
        """
        Connect to backend
        """
        self._backend.connect()

    def register_dataset(
        self,
        descriptor_id: str,
        intent: DataIntent = DataIntent.OUTGOING,
        **components: Any,
    ) -> ClientDatasetHandle:
        """
        Register a dataset intent locally and return a reusable handle
        """
        handle = ClientDatasetHandle(
            descriptor_id=descriptor_id,
            intent=intent,
            key=self.build_key(descriptor_id, **components),
        )
        self._dataset_handles[descriptor_id] = handle
        return handle

    def put_async(self, handle: ClientDatasetHandle, dataset: Dataset) -> Future[None]:
        """
        Asynchronously put a dataset
        """
        if handle.intent is not DataIntent.OUTGOING:
            raise ValueError(
                f"Handle '{handle.descriptor_id}' was registered as INCOMING; "
                "cannot use it for put_async"
            )
        return self._backend.put_dataset(handle.key, dataset)

    def get_async(self, handle: ClientDatasetHandle) -> Future[Dataset]:
        """
        Asynchronously fetch a dataset and return a future
        """
        if handle.intent is not DataIntent.INCOMING:
            raise ValueError(
                f"Handle '{handle.descriptor_id}' was registered as OUTGOING; "
                "cannot use it for get_async"
            )
        return self._backend.get_dataset(handle.key)

    def get_blocking(
        self, handle: ClientDatasetHandle, timeout: float | None = None
    ) -> Dataset:
        """
        Retrieve a dataset and block until available or timeout
        """
        return self.get_async(handle).result(timeout=timeout)

    def close(self) -> None:
        """
        Close any backend resources
        """
        self._backend.close()

    def build_key(self, key: str, **components: Any) -> str:
        """
        Construct a backend key locally from the configured key format
        """
        return self._base_key_format.format(key=key, **components)

    def _resolve_key_format(self) -> str:
        """
        Return the effective key format for this client
        """
        return self._base_key_format


class AdvancedClient(BasicClient):
    """
    Client to be used for workflows that use ROSE itself

    Main difference between this and the BasicClient is that the response from the
    ClientManager is used to configure the internals of the client. For now this
    is limited to the client identifier and key formatting rules.
    """

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
        """
        Register with the remote ROSE control plane and apply config

        registration: ClientRegistration emitted by the client to describe itself to the manager
        control_plane: ControlPlaneC
        """
        self._registration = registration
        self._control_plane = control_plane
        config = control_plane.register_client(registration)
        self.apply_manager_response(config)
        return config

    @_require_registered
    def register_outgoing_dataset(
        self, descriptor: RoseDataDescriptor
    ) -> ClientDatasetHandle:
        """
        Declare that this client will put data matching the given descriptor

        Registers the descriptor with the control plane as outgoing and returns
        a handle that must be passed to put_async
        """
        control_plane = self._control_plane
        if control_plane is None:
            raise ValueError(
                "AdvancedClient must be registered before declaring dataset intents"
            )
        unique_descriptor_id = control_plane.register_outgoing_descriptor(descriptor)
        handle = self.register_dataset(
            descriptor_id=unique_descriptor_id,
            intent=DataIntent.OUTGOING,
        )
        return handle

    @_require_registered
    def register_incoming_dataset(
        self, descriptor: RoseDataDescriptor
    ) -> ClientDatasetHandle:
        """
        Declare that this client will get data matching the given descriptor

        Registers the descriptor with the control plane as incoming and returns
        a handle that must be passed to get_async
        """
        control_plane = self._control_plane
        if control_plane is None:
            raise ValueError(
                "AdvancedClient must be registered before declaring dataset intents"
            )
        unique_descriptor_id = control_plane.register_incoming_descriptor(descriptor)
        handle = self.register_dataset(
            descriptor_id=unique_descriptor_id,
            intent=DataIntent.INCOMING,
        )
        return handle

    def apply_manager_response(self, config: ClientConfig | None) -> None:
        """
        Accept and store stateful response from manager for AdvancedClient
        """
        if config is None:
            raise ValueError("AdvancedClient requires a manager response")
        self._config = config
        self._rose_client_id = config.rose_client_id

    def put_async(self, handle: ClientDatasetHandle, dataset: Dataset) -> Future[None]:
        """
        Inject manager-issued client id into metadata before upload

        handle must be an OUTGOING handle obtained from register_outgoing_dataset
        """
        if handle.intent not in [DataIntent.OUTGOING, DataIntent.TWOWAY]:
            raise ValueError(
                f"Handle '{handle.descriptor_id}' was registered as INCOMING; "
                "cannot use it for put_async"
            )
        if self._rose_client_id:
            dataset = dataset.with_client_id(self._rose_client_id)
        return super().put_async(handle, dataset)

    def get_async(self, handle: ClientDatasetHandle) -> Future[Dataset]:
        """
        Asynchronously fetch a dataset using a pre-registered handle

        handle must be an INCOMING handle obtained from register_incoming_dataset
        """
        return super().get_async(handle)

    def build_key(self, key: str, **components: Any) -> str:
        """
        Construct a key locally using manager-provided formatting rules
        """
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
        """
        Return the manager-supplied key format when available
        """
        if self._config and self._config.key_format:
            return self._config.key_format
        return super()._resolve_key_format()
