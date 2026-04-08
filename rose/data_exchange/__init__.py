"""
Skeleton interfaces for ROSE data exchange clients and managers
"""

from rose.data_exchange.backend import DataBackend
from rose.data_exchange.client import AdvancedClient, BasicClient
from rose.data_exchange.client.models import (
    ClientConfig,
    ClientDatasetHandle,
    ClientRegistration,
    DataIntent,
)
from rose.data_exchange.client_manager import RoseClientManager
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.data_manager import DataManager, DatasetHandle
from rose.data_exchange.data_manager.models import DataEvent, SourceSpec, SubscriptionRequest
from rose.data_exchange.dataset import Dataset
from rose.data_exchange.dataset import (
    DataDescriptorValidator,
    ModificationPolicy,
    RoseDataDescriptor,
    ValidationPolicy,
)

__all__ = [
    "AdvancedClient",
    "BasicClient",
    "ClientConfig",
    "ClientDatasetHandle",
    "ClientRegistration",
    "ControlPlaneClient",
    "DataBackend",
    "DataIntent",
    "DataEvent",
    "DataDescriptorValidator",
    "DataManager",
    "Dataset",
    "DatasetHandle",
    "ModificationPolicy",
    "RoseClientManager",
    "RoseDataDescriptor",
    "SourceSpec",
    "SubscriptionRequest",
    "ValidationPolicy",
]
