"""
Catalogues: the unified internal API over every way bookworm can ask a
catalogue for a book. Other modules use the gateway and the canonical
models from here, never an adapter directly.
"""

from bookworm.modules.catalogues.gateway import CatalogueGateway, check_access
from bookworm.modules.catalogues.port import Adapter, AdapterContext, AdapterOptions
from bookworm.modules.catalogues.registry import register, registered_ids, unregister
from bookworm.modules.catalogues.schemas import (
    Attempt,
    BibRecord,
    BookQuery,
    CatalogueSearch,
    Holding,
    HoldingStatus,
    QueryKind,
    SearchOutcome,
    normalize_isbn,
)

__all__ = [
    "Adapter",
    "AdapterContext",
    "AdapterOptions",
    "Attempt",
    "BibRecord",
    "BookQuery",
    "CatalogueGateway",
    "CatalogueSearch",
    "Holding",
    "HoldingStatus",
    "QueryKind",
    "SearchOutcome",
    "check_access",
    "normalize_isbn",
    "register",
    "registered_ids",
    "unregister",
]
