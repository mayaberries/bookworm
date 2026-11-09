"""
The outside-world clients adapters use: one HTTP client and one (lazy)
browser per lookup.

WHY THE GATEWAY OWNS THEM AND ADAPTERS DON'T
    Opening a browser costs seconds and a few hundred MB; an HTTP client holds
    a connection pool. If every adapter opened its own, a lookup across ten
    catalogues would open ten. The gateway opens `Clients` once per lookup,
    hands it to each adapter through `AdapterContext`, and closes it at the
    end. The browser is launched only the first time an adapter asks for a
    page, so a lookup that only hits APIs never starts Chromium (and
    Playwright isn't even imported).
"""

from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Any

import httpx

from bookworm.shared.config import Settings


class Clients:
    def __init__(self, *, settings: Settings, http: httpx.AsyncClient, stack: AsyncExitStack) -> None:
        self.settings = settings
        self.http = http
        self._stack = stack
        self._browser: Any = None

    async def browser_page(self) -> Any:
        """A fresh Playwright page (in its own context, so cookies don't leak
        between catalogues). The caller closes it."""
        if self._browser is None:
            from playwright.async_api import async_playwright

            playwright = await self._stack.enter_async_context(async_playwright())
            self._browser = await playwright.chromium.launch(headless=self.settings.browser_headless)
            self._stack.push_async_callback(self._browser.close)
        context = await self._browser.new_context(user_agent=self.settings.user_agent)
        return await context.new_page()


@asynccontextmanager
async def open_clients(
    settings: Settings, *, transport: httpx.AsyncBaseTransport | None = None
) -> AsyncGenerator[Clients]:
    """`transport` lets tests replay recorded responses (httpx.MockTransport)
    instead of reaching the network."""
    async with AsyncExitStack() as stack:
        http = await stack.enter_async_context(
            httpx.AsyncClient(
                headers={"User-Agent": settings.user_agent},
                timeout=settings.http_timeout_seconds,
                follow_redirects=True,
                transport=transport,
            )
        )
        yield Clients(settings=settings, http=http, stack=stack)
