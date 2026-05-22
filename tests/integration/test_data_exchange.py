from __future__ import annotations

import numpy as np
import pytest

from rose.data_exchange.client import AdvancedClient
from rose.data_exchange.control_plane import ControlPlaneClient
from rose.data_exchange.data_manager import DataManager
from rose.data_exchange.data_manager.models import SourceSpec
from rose.data_exchange.dataset import Dataset, RoseDataDescriptor


def test_register_single_descriptor_starts_incomplete(
	data_manager: DataManager,
	client_control_plane: ControlPlaneClient,
) -> None:
	"""
	Registering one descriptor with one expected source is incomplete before posting
	"""
	descriptor = RoseDataDescriptor(
		descriptor_id="dataset-1",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [4, 4],
			}
		},
	)
	handle = data_manager.register_descriptor(descriptor)

	handle.add_source(SourceSpec(source_id="sim-rank-0", expected_parts=1))

	assert handle.is_complete is False


def test_client_put_marks_dataset_complete(
	client1: AdvancedClient,
	data_manager: DataManager,
) -> None:
	"""
	Putting a dataset through the client marks the dataset as complete
	"""
	canonical_descriptor = RoseDataDescriptor(
		descriptor_id="dataset-2",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [2, 2],
			}
		},
	)
	manager_handle = data_manager.register_descriptor(canonical_descriptor)

	client_descriptor = RoseDataDescriptor(
		descriptor_id="dataset-2",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [2, 2],
			}
		},
	)
	client_handle = client1.register_outgoing_dataset(client_descriptor)
	assert client_handle.descriptor_id == manager_handle.descriptor_id
	assert data_manager.get_descriptor(client_handle.descriptor_id) is canonical_descriptor

	manager_handle.add_source(SourceSpec(source_id="rose-client-1", expected_parts=1))

	dataset = Dataset(name="dataset-2")
	dataset.add_tensor("state", np.ones((2, 2)))

	client1.put_async(client_handle, dataset).result(timeout=1.0)

	assert manager_handle.is_complete is True

def test_unregistered_descriptor_fails(client1: AdvancedClient, data_manager: DataManager) -> None:
	client_descriptor = RoseDataDescriptor(
		descriptor_id="dataset-3",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [2, 2],
			}
		},
	)
	# ValueError is the exception here for the mocked out data manager
	with pytest.raises(ValueError):
		client1.register_outgoing_dataset(client_descriptor)
	with pytest.raises(ValueError):
		client1.register_incoming_dataset(client_descriptor)

def test_producer_consumer(
	client1: AdvancedClient,
	client2: AdvancedClient,
	data_manager: DataManager,
) -> None:
	"""
	Putting a dataset through the client marks the dataset as complete
	"""

  ## Main ROSE script (on head node)
	canonical_descriptor = RoseDataDescriptor(
		descriptor_id="dataset-3",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [2, 2],
			}
		},
	)
	manager_handle = data_manager.register_descriptor(canonical_descriptor)
	manager_handle.add_source(SourceSpec(source_id="rose-client-1", expected_parts=1))

  # Common descriptor known to both producer and consumer clients
	client_descriptor = RoseDataDescriptor(
		descriptor_id="dataset-3",
		datafields={
			"state": {
				"dtype": "float64",
				"shape": [2, 2],
			}
		},
	)

  # Client 1 produces the dataset (on compute node 1)
	c1_handle = client1.register_outgoing_dataset(client_descriptor)
	dataset = Dataset(name="dataset-3")
	dataset.add_tensor("state", np.ones((2, 2)))
	client1.put_async(c1_handle, dataset).result(timeout=1.0)

  # Client 2 consumes the dataset (on compute node 2)
	c2_handle = client2.register_incoming_dataset(client_descriptor)
	dataset = client2.get_async(c2_handle).result(timeout=1.0)
	assert np.array_equal(dataset.tensors["state"], np.ones((2, 2)))

	assert manager_handle.is_complete is True
