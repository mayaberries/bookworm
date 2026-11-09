"""
The canonical book models: the one shape every catalogue's answer is turned
into, whatever it came from (a REST API's JSON, a results page's HTML, a
browser session, MARC).

WHY ONE SHAPE
    The lookup service compares and reports across catalogues. If it saw
    VuFind JSON from one and Aleph HTML from another, every rule would branch
    on the source. Adapters translate at the boundary (an anti-corruption
    layer); nothing past the gateway knows how a catalogue answered. A field
    that one source can't fill is None, never guessed.

Raw shapes (an API's JSON, a parsed HTML row) are the adapter's own models,
named `Raw*`, and never leave its package. See the `create-adapter` skill.
"""

import re
from datetime import date, datetime
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, HttpUrl, model_validator

from bookworm.shared.schemas import FrozenModel, InputModel


def normalize_isbn(value: str) -> str:
    """Digits (and a final X) only, as ISBN-13. Catalogues print ISBNs with
    hyphens, spaces, '(pbk.)' and as ISBN-10; comparing them needs one form."""
    compact = re.sub(r"[^0-9Xx]", "", value).upper()
    if len(compact) == 10 and compact[:9].isdigit():
        body = "978" + compact[:9]
        check = (10 - sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(body)) % 10) % 10
        return body + str(check)
    if len(compact) == 13 and compact.isdigit():
        return compact
    raise ValueError(f"{value!r} isn't an ISBN: expected 10 or 13 digits (an ISBN-10 may end in X)")


Isbn = Annotated[str, AfterValidator(normalize_isbn)]


def _blank_to_none(value: object) -> object:
    return None if isinstance(value, str) and not value.strip() else value


class QueryKind(StrEnum):
    isbn = "isbn"
    title_author = "title_author"


class BookQuery(InputModel):
    """What a person is looking for: an ISBN, or a title and/or author."""

    isbn: Annotated[Isbn | None, BeforeValidator(_blank_to_none)] = None
    title: Annotated[str | None, BeforeValidator(_blank_to_none)] = None
    author: Annotated[str | None, BeforeValidator(_blank_to_none)] = None

    @model_validator(mode="after")
    def _one_kind(self) -> "BookQuery":
        if self.isbn and (self.title or self.author):
            raise ValueError("give either an isbn, or a title and/or author, not both")
        if not (self.isbn or self.title or self.author):
            raise ValueError("give an isbn, or a title and/or author")
        return self

    @property
    def kind(self) -> QueryKind:
        return QueryKind.isbn if self.isbn else QueryKind.title_author


class HoldingStatus(StrEnum):
    available = "available"  # on the shelf, can be borrowed or read
    on_loan = "on_loan"
    on_site_only = "on_site_only"  # reference, reserve, consultation only
    unavailable = "unavailable"  # lost, being processed, in repair...
    unknown = "unknown"  # the catalogue said something the adapter can't map


class Holding(FrozenModel):
    """One copy, as the catalogue lists it."""

    location: str | None = Field(default=None, description="The catalogue's name for where the copy is.")
    location_code: str | None = Field(default=None, description="Matched against Library.catalogue_location.")
    call_number: str | None = None
    status: HoldingStatus = HoldingStatus.unknown
    status_text: str | None = Field(default=None, description="The catalogue's own words, kept for auditing.")
    due_date: date | None = None


class BibRecord(FrozenModel):
    """One catalogue record: a title as one catalogue describes it."""

    record_id: str
    url: HttpUrl | None = None
    title: str
    authors: tuple[str, ...] = ()
    isbns: tuple[Isbn, ...] = ()
    year: int | None = None
    publisher: str | None = None
    # None: the adapter didn't fetch copies (the source doesn't say, or it
    # costs another request). (): it fetched them and there are none.
    holdings: tuple[Holding, ...] | None = None


class SearchOutcome(StrEnum):
    answered = "answered"  # an access method answered; `records` may be empty
    no_access = "no_access"  # no access methods configured
    not_allowed = "not_allowed"  # automation disallowed; never queried
    failed = "failed"  # every access method failed; see `attempts`


class Attempt(FrozenModel):
    adapter: str
    error: str  # the CatalogueError subclass name, e.g. "CatalogueChangedError"
    detail: str


class CatalogueSearch(FrozenModel):
    """What the gateway returns for one catalogue."""

    catalogue: str
    outcome: SearchOutcome
    answered_by: str | None = None
    records: tuple[BibRecord, ...] = ()
    attempts: tuple[Attempt, ...] = ()
    searched_at: datetime
