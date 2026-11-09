"""
The reference adapters are registered for each test and removed after it:
the registry is process-global, so a test that registers something must not
leave it for the next (the write-tests skill's "autouse reset").
"""

from collections.abc import Iterator

import pytest

from bookworm.modules.catalogues import register, unregister
from tests._adapters import fake


@pytest.fixture(autouse=True)
def reference_adapters() -> Iterator[None]:
    fake.FakeMemoryAdapter.searches.clear()
    for adapter in fake.ALL:
        register(adapter)
    yield
    for adapter in fake.ALL:
        unregister(adapter.id)
