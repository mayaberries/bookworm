"""
The adapter registry: adapter id → class.

Adapters register themselves with `@register` when their module is imported,
and `adapters/__init__.py` imports every adapter module explicitly, so the
list of what bookworm can talk to is one file, readable without running it.
"""

import re

from bookworm.modules.catalogues.port import Adapter
from bookworm.shared.errors import NotFoundError

ADAPTER_ID = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")

_ADAPTERS: dict[str, type[Adapter]] = {}


def register[A: type[Adapter]](adapter: A) -> A:
    if not ADAPTER_ID.match(adapter.id):
        raise ValueError(f"{adapter.__name__}.id = {adapter.id!r}: expected '<system>.<method>'")
    if adapter.id in _ADAPTERS and _ADAPTERS[adapter.id] is not adapter:
        raise ValueError(
            f"adapter id {adapter.id!r} is already registered by {_ADAPTERS[adapter.id].__name__}"
        )
    if not adapter.supports:
        raise ValueError(f"{adapter.__name__}.supports is empty")
    _ADAPTERS[adapter.id] = adapter
    return adapter


def unregister(adapter_id: str) -> None:
    """Tests only: drop an adapter a test registered."""
    _ADAPTERS.pop(adapter_id, None)


def get_adapter_class(adapter_id: str) -> type[Adapter]:
    try:
        return _ADAPTERS[adapter_id]
    except KeyError:
        known = ", ".join(sorted(_ADAPTERS)) or "none yet"
        raise NotFoundError(f"No adapter '{adapter_id}' is registered (registered: {known}).") from None


def registered_ids() -> list[str]:
    return sorted(_ADAPTERS)
