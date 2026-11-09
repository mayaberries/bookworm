"""
The gateway: the one entry point for searching a catalogue, whatever its
access methods.

It reads the catalogue's record and decides *whether* and *how* to ask:

    automation not allowed → not_allowed, no request sent (unknown counts as no)
    no access methods      → no_access
    otherwise, each access method in order:
        unknown adapter, unsupported query kind, bad options  → recorded, next
        CatalogueError while searching                        → recorded, next
        records (even [])                                     → answered, stop
    all of them failed     → failed, with every attempt

Failures are values here, not exceptions: one catalogue failing never stops
a lookup across twenty. Programming errors (anything that isn't a
CatalogueError) still raise, so a bug in an adapter is loud.
"""

from datetime import UTC, datetime

from pydantic import ValidationError

from bookworm.modules.catalogues import adapters as _adapters  # noqa: F401  (registers every adapter)
from bookworm.modules.catalogues.port import AdapterContext, Throttle
from bookworm.modules.catalogues.registry import get_adapter_class
from bookworm.modules.catalogues.schemas import Attempt, BookQuery, CatalogueSearch, SearchOutcome
from bookworm.modules.directory import Automation, Catalogue, DirectoryIssue
from bookworm.shared.clients import Clients
from bookworm.shared.errors import CatalogueError, NotFoundError


class CatalogueGateway:
    def __init__(self, *, clients: Clients) -> None:
        self.clients = clients
        self._throttles: dict[str, Throttle] = {}

    def _throttle_for(self, catalogue: Catalogue) -> Throttle:
        if catalogue.slug not in self._throttles:
            self._throttles[catalogue.slug] = Throttle(catalogue.min_seconds_between_requests)
        return self._throttles[catalogue.slug]

    async def search(self, *, catalogue: Catalogue, query: BookQuery) -> CatalogueSearch:
        now = datetime.now(UTC)
        if catalogue.automation is not Automation.allowed:
            return CatalogueSearch(
                catalogue=catalogue.slug, outcome=SearchOutcome.not_allowed, searched_at=now
            )
        if not catalogue.access:
            return CatalogueSearch(catalogue=catalogue.slug, outcome=SearchOutcome.no_access, searched_at=now)

        context = AdapterContext(
            catalogue=catalogue, clients=self.clients, throttle=self._throttle_for(catalogue)
        )
        attempts: list[Attempt] = []
        for method in catalogue.access:
            try:
                adapter_class = get_adapter_class(method.adapter)
            except NotFoundError as exc:
                attempts.append(Attempt(adapter=method.adapter, error="NotFoundError", detail=exc.detail))
                continue
            if query.kind not in adapter_class.supports:
                attempts.append(
                    Attempt(
                        adapter=method.adapter,
                        error="UnsupportedQueryError",
                        detail=f"can't search by {query.kind.value}",
                    )
                )
                continue
            try:
                options = adapter_class.Options.model_validate(method.options)
            except ValidationError as exc:
                attempts.append(Attempt(adapter=method.adapter, error="InvalidOptions", detail=str(exc)))
                continue

            try:
                records = await adapter_class(context=context, options=options).search(query)
            except CatalogueError as exc:
                attempts.append(Attempt(adapter=method.adapter, error=type(exc).__name__, detail=exc.detail))
                continue
            return CatalogueSearch(
                catalogue=catalogue.slug,
                outcome=SearchOutcome.answered,
                answered_by=method.adapter,
                records=tuple(records),
                attempts=tuple(attempts),
                searched_at=now,
            )

        return CatalogueSearch(
            catalogue=catalogue.slug, outcome=SearchOutcome.failed, attempts=tuple(attempts), searched_at=now
        )


def check_access(catalogues: list[Catalogue]) -> list[DirectoryIssue]:
    """The record check's half that needs adapters: every access entry names
    a registered adapter, and its options match that adapter's `Options`.
    Listing access methods also requires `automation: allowed` and the date
    robots.txt was checked, so nobody wires up a catalogue without looking."""
    issues: list[DirectoryIssue] = []
    for catalogue in catalogues:
        path = f"data/catalogues/{catalogue.slug}.md"
        if catalogue.access and (
            catalogue.automation is not Automation.allowed or catalogue.robots_checked_on is None
        ):
            issues.append(
                DirectoryIssue(
                    path=path,
                    detail="access: listing access methods needs `automation: allowed` and "
                    "`robots_checked_on`, after checking robots.txt and the terms",
                )
            )
        for i, method in enumerate(catalogue.access):
            try:
                adapter_class = get_adapter_class(method.adapter)
            except NotFoundError as exc:
                issues.append(DirectoryIssue(path=path, detail=f"access.{i}.adapter: {exc.detail}"))
                continue
            try:
                adapter_class.Options.model_validate(method.options)
            except ValidationError as exc:
                issues.append(DirectoryIssue(path=path, detail=f"access.{i}.options: {exc}"))
    return issues
