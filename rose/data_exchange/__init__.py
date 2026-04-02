"""Skeleton interfaces for ROSE data exchange clients and managers."""

from rose.data_exchange.backend import DataBackend
from rose.data_exchange.client import AdvancedClient, BasicClient
from rose.data_exchange.client_manager import RoseClientManager
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.data_manager import DataManager, DatasetHandle
from rose.data_exchange.dataset import Dataset
from rose.data_exchange.descriptors import (
    AppDataDescriptor,
    DataDescriptorValidator,
    DescriptorField,
    ModificationPolicy,
    RoseDataDescriptor,
    ValidationPolicy,
)
from rose.data_exchange.models import (
    ClientConfig,
    ClientRegistration,
    DataEvent,
    SourceSpec,
    SubscriptionRequest,
)

__all__ = [
    "AdvancedClient",
    "AppDataDescriptor",
    "BasicClient",
    "ClientConfig",
    "ClientRegistration",
    "ControlPlaneClient",
    "DataBackend",
    "DataEvent",
    "DataDescriptorValidator",
    "DataManager",
    "Dataset",
    "DatasetHandle",
    "DescriptorField",
    "ModificationPolicy",
    "RoseClientManager",
    "RoseDataDescriptor",
    "SourceSpec",
    "SubscriptionRequest",
    "ValidationPolicy",
]
