"""
The directory's records: one `Library` per file in `data/libraries/`, one
`Catalogue` per file in `data/catalogues/`.

WHY TWO KINDS OF RECORD
    A catalogue is software at a URL; a library is a building with shelves.
    They're not one-to-one: UNAM's Descubridor covers dozens of UNAM libraries,
    and most alcaldía branches have no catalogue at all. Adapters talk to
    catalogues; people go to libraries. A library points at the catalogue that
    lists its books (`catalogue`), plus the code that catalogue uses for it
    (`catalogue_location`), so one search can answer for every library that
    shares the catalogue.

WHAT A RECORD MODEL IS
    The `*Record` models are exactly the frontmatter's fields (the files are
    our tables), validated with `InputModel` so a typo'd key is an error. The
    repository adds `slug` (the file name) and `notes` (the Markdown body)
    to build `Library` / `Catalogue`, the shapes the rest of the code uses.
"""

from datetime import date
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AfterValidator, Field, HttpUrl, StringConstraints

from bookworm.shared.schemas import CoreModel, InputModel

Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)]


class Alcaldia(StrEnum):
    alvaro_obregon = "Álvaro Obregón"
    azcapotzalco = "Azcapotzalco"
    benito_juarez = "Benito Juárez"
    coyoacan = "Coyoacán"
    cuajimalpa = "Cuajimalpa de Morelos"
    cuauhtemoc = "Cuauhtémoc"
    gustavo_a_madero = "Gustavo A. Madero"
    iztacalco = "Iztacalco"
    iztapalapa = "Iztapalapa"
    magdalena_contreras = "La Magdalena Contreras"
    miguel_hidalgo = "Miguel Hidalgo"
    milpa_alta = "Milpa Alta"
    tlahuac = "Tláhuac"
    tlalpan = "Tlalpan"
    venustiano_carranza = "Venustiano Carranza"
    xochimilco = "Xochimilco"


class LibraryKind(StrEnum):
    public = "public"  # alcaldía, city or federal public library
    national = "national"
    academic = "academic"  # a university's library
    specialized = "specialized"  # research institutes, embassies, foundations
    other = "other"


class Lending(StrEnum):
    public = "public"  # anyone can borrow (perhaps with a free card)
    members_only = "members_only"  # e.g. UNAM community only; the public may read on site
    on_site_only = "on_site_only"
    unknown = "unknown"


class VerificationStatus(StrEnum):
    verified = "verified"  # someone loaded the page or called and checked
    inferred = "inferred"  # deduced from search results, docs or similar sites
    unverified = "unverified"


class Verification(InputModel):
    status: VerificationStatus = VerificationStatus.unverified
    checked_on: date | None = None
    source: str | None = Field(default=None, description="Where the record's data came from, briefly.")


class Contact(InputModel):
    phone: str | None = None
    email: str | None = None
    website: HttpUrl | None = None


# --- Catalogues -------------------------------------------------------------


class CatalogueSystem(StrEnum):
    """The software behind a catalogue. Descriptive: what picks the code
    that talks to it is each access entry's `adapter`."""

    vufind = "vufind"
    aleph = "aleph"
    koha = "koha"
    janium = "janium"
    custom = "custom"
    unknown = "unknown"


class Automation(StrEnum):
    """Whether we may query it automatically, from robots.txt and its terms.
    Bookworm only sends requests to `allowed` catalogues: `unknown` is
    treated like `disallowed` until someone checks (docs/DECISIONS.md)."""

    allowed = "allowed"
    disallowed = "disallowed"
    unknown = "unknown"


def _check_adapter_id(value: str) -> str:
    system, _, method = value.partition(".")
    if not system or not method or "." in method:
        raise ValueError(f"{value!r} isn't an adapter id: expected '<system>.<method>', e.g. 'vufind.api'")
    return value


AdapterId = Annotated[str, AfterValidator(_check_adapter_id)]


class AccessMethod(InputModel):
    """One way to query a catalogue. A catalogue lists them in the order to
    try; the gateway falls through to the next when one fails."""

    adapter: AdapterId = Field(description="Registered adapter id, '<system>.<method>', e.g. 'vufind.api'.")
    # Validated by the adapter's own `Options` model when it's built, since
    # only the adapter knows what it needs.
    options: dict[str, Any] = Field(default_factory=dict)


class CatalogueRecord(InputModel):
    name: str = Field(min_length=1)
    system: CatalogueSystem = CatalogueSystem.unknown
    system_version: str | None = None
    base_url: HttpUrl
    automation: Automation = Automation.unknown
    robots_checked_on: date | None = None
    min_seconds_between_requests: float = Field(default=2.0, ge=0)
    # Empty while nobody has written or configured an adapter for it: the
    # catalogue is known, but lookups report it as "check by hand".
    access: list[AccessMethod] = Field(default_factory=list)
    verification: Verification = Field(default_factory=Verification)


class Catalogue(CatalogueRecord):
    slug: Slug
    notes: str = ""


# --- Libraries --------------------------------------------------------------


class LibraryRecord(InputModel):
    name: str = Field(min_length=1)
    kind: LibraryKind
    alcaldia: Alcaldia | None = None
    address: str | None = None
    contact: Contact = Field(default_factory=Contact)
    # The catalogue that lists this library's books, by slug. None when it
    # has no online catalogue: lookups say to call or visit.
    catalogue: Slug | None = None
    # How that catalogue names this library (a VuFind "building" facet, an
    # Aleph sub-library code...). None when the catalogue is only this library's.
    catalogue_location: str | None = None
    lending: Lending = Lending.unknown
    interlibrary_loan: list[Slug] = Field(
        default_factory=list, description="Library slugs it has agreements with."
    )
    verification: Verification = Field(default_factory=Verification)
    tags: list[str] = Field(default_factory=list)


class Library(LibraryRecord):
    slug: Slug
    notes: str = ""


class DirectoryIssue(CoreModel):
    """One problem `check_records` found: which file, and what's wrong."""

    path: str
    detail: str
