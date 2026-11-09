"""
What a lookup answers: for each library asked about, can I find this book
there, and how sure are we.
"""

from datetime import datetime
from enum import StrEnum

from bookworm.modules.catalogues import BibRecord, BookQuery, Holding
from bookworm.shared.schemas import FrozenModel


class LibraryOutcome(StrEnum):
    available = "available"  # at least one copy here is on the shelf
    held_not_available = "held_not_available"  # copies here, none on the shelf now
    held_status_unknown = "held_status_unknown"  # found, but no word on where or whether it's out
    not_found = "not_found"  # the catalogue answered and this library has no copy
    check_manually = "check_manually"  # no online catalogue, or we may not query it
    failed = "failed"  # the catalogue couldn't be searched just now


class Match(StrEnum):
    exact = "exact"  # the record lists the ISBN asked for
    possible = "possible"  # title/author search, or the record lists no ISBN


class FoundRecord(FrozenModel):
    record: BibRecord
    match: Match
    # This library's copies of it; None when the catalogue didn't list copies.
    holdings: tuple[Holding, ...] | None


class LibraryAvailability(FrozenModel):
    library: str
    library_name: str
    catalogue: str | None
    outcome: LibraryOutcome
    found: tuple[FoundRecord, ...] = ()
    detail: str | None = None  # why: "no online catalogue", the failed attempts...


class AvailabilityReport(FrozenModel):
    query: BookQuery
    results: tuple[LibraryAvailability, ...]
    generated_at: datetime
