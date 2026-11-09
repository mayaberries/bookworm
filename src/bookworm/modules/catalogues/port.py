"""
The port: what every catalogue adapter is, and what it's given.

THE PATTERN
    Ports and adapters. The lookup service needs one operation, "search this
    catalogue for this book", and must not care whether the answer came from
    a REST API, an HTML page or a headless browser. `Adapter` is that
    operation's contract; each way of talking to a kind of catalogue is one
    subclass, registered under an id `<system>.<method>` (`vufind.api`,
    `vufind.html`, `vasconcelos.browser`). A catalogue's record lists the ids
    to try, in order (`access:`), with per-catalogue `options`. Adding a
    catalogue that runs software we already support is a record, not code.

WHAT AN ADAPTER MAY TOUCH
    Only `AdapterContext`: the catalogue's record, its validated options, and
    the paced, error-translating `get()` / `page()`. Never settings, the
    directory, other adapters or the filesystem. That keeps every adapter
    testable with a recorded response and nothing else.

WHY `get()` AND `page()` ARE ON THE CONTEXT
    Two things every adapter needs and would each get slightly wrong: pacing
    (the catalogue's `min_seconds_between_requests`, shared by all its
    adapters during a lookup) and turning httpx/Playwright failures into
    bookworm's `Catalogue*Error`s. Done once here, adapters only parse.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, ClassVar

import httpx

from bookworm.modules.catalogues.schemas import BibRecord, BookQuery, QueryKind
from bookworm.modules.directory import Catalogue
from bookworm.shared.clients import Clients
from bookworm.shared.errors import CatalogueBlockedError, CatalogueUnavailableError
from bookworm.shared.schemas import InputModel


class AdapterOptions(InputModel):
    """Base for an adapter's `Options`: what a catalogue record's
    `access[].options` may say to it. `extra="forbid"`, so a typo is an error
    when the record is checked, not a silently ignored option."""


class Throttle:
    """At most one request per `interval` seconds to one catalogue, across
    all its adapters and concurrent tasks in a lookup."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._lock = asyncio.Lock()
        self._last = float("-inf")

    async def wait(self) -> None:
        async with self._lock:
            delay = self._last + self.interval - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            self._last = time.monotonic()


class AdapterContext:
    def __init__(self, *, catalogue: Catalogue, clients: Clients, throttle: Throttle) -> None:
        self.catalogue = catalogue
        self._clients = clients
        self._throttle = throttle

    @property
    def base_url(self) -> str:
        return str(self.catalogue.base_url).rstrip("/")

    async def get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        """GET, paced, with failures already translated: returns only 2xx/3xx."""
        await self._throttle.wait()
        try:
            response = await self._clients.http.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise CatalogueUnavailableError(f"{url}: timed out") from exc
        except httpx.TransportError as exc:
            raise CatalogueUnavailableError(f"{url}: {exc.__class__.__name__}: {exc}") from exc
        if response.status_code in (401, 403, 429):
            raise CatalogueBlockedError(f"{url}: HTTP {response.status_code}")
        if response.status_code >= 400:
            raise CatalogueUnavailableError(f"{url}: HTTP {response.status_code}")
        return response

    async def page(self) -> Any:
        """A fresh Playwright page, paced. The adapter closes it
        (`await page.context.close()`), in a `finally`."""
        await self._throttle.wait()
        return await self._clients.browser_page()


class Adapter(ABC):
    """One way of searching one kind of catalogue. Subclass, set the class
    attributes, implement `search`, and register it (`registry.register`)."""

    id: ClassVar[str]  # "<system>.<method>"
    supports: ClassVar[frozenset[QueryKind]]
    Options: ClassVar[type[AdapterOptions]] = AdapterOptions

    def __init__(self, *, context: AdapterContext, options: AdapterOptions) -> None:
        self.context = context
        self.options = options

    @abstractmethod
    async def search(self, query: BookQuery) -> list[BibRecord]:
        """Every record the catalogue returns for the query, in canonical
        form. Raise a `CatalogueError` subclass when it can't answer; return
        [] only when it answered "nothing found"."""
