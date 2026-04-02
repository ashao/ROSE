"""Backend abstraction for datastore implementations."""

from __future__ import annotations

from concurrent.futures import Future
from typing import Protocol

from rose.data_exchange.dataset import Dataset


class DataBackend(Protocol):
    """Protocol implemented by concrete datastore backends."""

    def connect(self) -> None:
        """Establish backend connection using existing configuration."""

    def put_dataset(self, key: str, dataset: Dataset) -> Future[None]:
        """Store a dataset asynchronously and return a completion future."""

    def get_dataset(self, key: str) -> Future[Dataset]:
        """Fetch a dataset asynchronously and return a future."""

    def close(self) -> None:
        """Release backend resources."""
