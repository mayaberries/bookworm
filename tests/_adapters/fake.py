"""
Reference adapters: real implementations of the port that the suite uses
instead of real catalogues, the way Kalens and Xolo test against a reference
host in tests/_host/. They aren't mocks of our code; they're the smallest
adapters that honour the contract.

- `fake.memory` answers from its options: the records to return, or the
  CatalogueError to raise. It logs each search, so tests can count them.
- `fake.http` does what a real API adapter does: GETs `<base_url>/search`,
  parses the JSON through `Raw*` models and maps it to canonical records.
  Tests feed it recorded responses through httpx.MockTransport.
"""

from typing import ClassVar

from pydantic import ValidationError

from bookworm.modules.catalogues import (
    Adapter,
    AdapterOptions,
    BibRecord,
    BookQuery,
    Holding,
    HoldingStatus,
    QueryKind,
)
from bookworm.shared import errors
from bookworm.shared.schemas import CoreModel


class FakeMemoryOptions(AdapterOptions):
    records: list[BibRecord] = []
    fail_with: str | None = None  # a CatalogueError subclass name


class FakeMemoryAdapter(Adapter):
    id = "fake.memory"
    supports = frozenset({QueryKind.isbn, QueryKind.title_author})
    Options = FakeMemoryOptions

    searches: ClassVar[list[tuple[str, BookQuery]]] = []

    async def search(self, query: BookQuery) -> list[BibRecord]:
        assert isinstance(self.options, FakeMemoryOptions)
        FakeMemoryAdapter.searches.append((self.context.catalogue.slug, query))
        if self.options.fail_with:
            raise getattr(errors, self.options.fail_with)(f"fake failure: {self.options.fail_with}")
        return self.options.records


class FakeIsbnOnlyAdapter(FakeMemoryAdapter):
    id = "fake.isbn_only"
    supports = frozenset({QueryKind.isbn})


# --- fake.http: the shape of a real API adapter ------------------------------


class RawCopy(CoreModel):
    branch: str
    shelfmark: str | None = None
    state: str


class RawHit(CoreModel):
    id: str
    title: str
    isbn: list[str] = []
    copies: list[RawCopy] = []


class RawSearchResponse(CoreModel):
    hits: list[RawHit]


STATUS_MAP = {"on shelf": HoldingStatus.available, "checked out": HoldingStatus.on_loan}


def to_bib_record(hit: RawHit, *, base_url: str) -> BibRecord:
    return BibRecord(
        record_id=hit.id,
        url=f"{base_url}/record/{hit.id}",
        title=hit.title,
        isbns=tuple(hit.isbn),
        holdings=tuple(
            Holding(
                location=c.branch,
                location_code=c.branch,
                call_number=c.shelfmark,
                status=STATUS_MAP.get(c.state, HoldingStatus.unknown),
                status_text=c.state,
            )
            for c in hit.copies
        ),
    )


class FakeHttpAdapter(Adapter):
    id = "fake.http"
    supports = frozenset({QueryKind.isbn})

    async def search(self, query: BookQuery) -> list[BibRecord]:
        response = await self.context.get(f"{self.context.base_url}/search", params={"isbn": query.isbn})
        try:
            raw = RawSearchResponse.model_validate_json(response.content)
        except ValidationError as exc:
            raise errors.CatalogueChangedError(f"/search: unexpected JSON: {exc}") from exc
        return [to_bib_record(hit, base_url=self.context.base_url) for hit in raw.hits]


ALL = [FakeMemoryAdapter, FakeIsbnOnlyAdapter, FakeHttpAdapter]
