"""
Lookup: "is this book at these libraries?", across every catalogue that
can answer. The CLI's `find` command calls this and nothing else.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx

from bookworm.modules.catalogues import CatalogueGateway
from bookworm.modules.directory import build_directory_service
from bookworm.modules.lookup.schemas import (
    AvailabilityReport,
    FoundRecord,
    LibraryAvailability,
    LibraryOutcome,
    Match,
)
from bookworm.modules.lookup.service import LookupService
from bookworm.shared.clients import open_clients
from bookworm.shared.config import Settings


@asynccontextmanager
async def open_lookup_service(
    settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
) -> AsyncGenerator[LookupService]:
    """The service with its clients open; they close when the block exits."""
    async with open_clients(settings, transport=transport) as clients:
        yield LookupService(
            directory=build_directory_service(settings.data_dir),
            gateway=CatalogueGateway(clients=clients),
            max_concurrent_catalogues=settings.max_concurrent_catalogues,
        )


__all__ = [
    "AvailabilityReport",
    "FoundRecord",
    "LibraryAvailability",
    "LibraryOutcome",
    "LookupService",
    "Match",
    "open_lookup_service",
]
