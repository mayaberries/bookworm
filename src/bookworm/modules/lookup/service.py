"""
The lookup use case: "is this book at these libraries?"

    libraries (all, or the slugs asked for)
      → the catalogues they point at, each searched ONCE, concurrently
      → each library's share of its catalogue's answer (its holdings, by
        `catalogue_location`)
      → one LibraryAvailability per library

Searching per catalogue rather than per library matters: UNAM's Descubridor
answers for dozens of libraries with one request.
"""

import asyncio
from datetime import UTC, datetime

from bookworm.modules.catalogues import (
    BibRecord,
    BookQuery,
    CatalogueGateway,
    CatalogueSearch,
    Holding,
    HoldingStatus,
    QueryKind,
    SearchOutcome,
)
from bookworm.modules.directory import DirectoryService, Library
from bookworm.modules.lookup.schemas import (
    AvailabilityReport,
    FoundRecord,
    LibraryAvailability,
    LibraryOutcome,
    Match,
)


class LookupService:
    def __init__(
        self, *, directory: DirectoryService, gateway: CatalogueGateway, max_concurrent_catalogues: int
    ) -> None:
        self.directory = directory
        self.gateway = gateway
        self.max_concurrent_catalogues = max_concurrent_catalogues

    async def find(self, *, query: BookQuery, library_slugs: list[str] | None = None) -> AvailabilityReport:
        now = datetime.now(UTC)
        if library_slugs:
            libraries = [self.directory.get_library(slug=slug) for slug in library_slugs]
        else:
            libraries = self.directory.list_libraries()
        catalogues = self.directory.catalogues_for(libraries=libraries)

        semaphore = asyncio.Semaphore(self.max_concurrent_catalogues)

        async def search(slug: str) -> CatalogueSearch:
            async with semaphore:
                return await self.gateway.search(catalogue=catalogues[slug], query=query)

        searches = await asyncio.gather(*(search(slug) for slug in catalogues))
        by_catalogue = {s.catalogue: s for s in searches}

        return AvailabilityReport(
            query=query,
            results=tuple(
                self._for_library(lib, by_catalogue.get(lib.catalogue or ""), query) for lib in libraries
            ),
            generated_at=now,
        )

    def _for_library(
        self, library: Library, search: CatalogueSearch | None, query: BookQuery
    ) -> LibraryAvailability:
        base = {"library": library.slug, "library_name": library.name, "catalogue": library.catalogue}

        if search is None:
            return LibraryAvailability(
                **base, outcome=LibraryOutcome.check_manually, detail="No online catalogue: call or visit."
            )
        if search.outcome is SearchOutcome.not_allowed:
            return LibraryAvailability(
                **base,
                outcome=LibraryOutcome.check_manually,
                detail="Its catalogue doesn't allow automated searches, or nobody has checked yet: "
                "search it by hand.",
            )
        if search.outcome is SearchOutcome.no_access:
            return LibraryAvailability(
                **base,
                outcome=LibraryOutcome.check_manually,
                detail="Bookworm can't search its catalogue yet: search it by hand.",
            )
        if search.outcome is SearchOutcome.failed:
            detail = "; ".join(f"{a.adapter}: {a.error}: {a.detail}" for a in search.attempts)
            return LibraryAvailability(**base, outcome=LibraryOutcome.failed, detail=detail)

        found = tuple(
            item
            for item in (self._share(record, library, query) for record in search.records)
            if item.holdings is None or item.holdings
        )
        return LibraryAvailability(**base, outcome=_outcome(found), found=found)

    @staticmethod
    def _share(record: BibRecord, library: Library, query: BookQuery) -> FoundRecord:
        match = Match.exact if query.kind is QueryKind.isbn and query.isbn in record.isbns else Match.possible
        holdings = record.holdings
        if holdings is not None and library.catalogue_location is not None:
            holdings = tuple(
                h for h in holdings if library.catalogue_location in (h.location_code, h.location)
            )
        return FoundRecord(record=record, match=match, holdings=holdings)


def _outcome(found: tuple[FoundRecord, ...]) -> LibraryOutcome:
    if not found:
        return LibraryOutcome.not_found
    holdings: list[Holding] = [h for item in found for h in (item.holdings or ())]
    if any(h.status is HoldingStatus.available for h in holdings):
        return LibraryOutcome.available
    if any(item.holdings is None for item in found) or any(
        h.status is HoldingStatus.unknown for h in holdings
    ):
        return LibraryOutcome.held_status_unknown
    return LibraryOutcome.held_not_available
