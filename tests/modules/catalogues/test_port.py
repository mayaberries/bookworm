"""
AdapterContext.get(): every adapter's HTTP goes through it, so the error
translation is tested once, here, with recorded or synthetic responses
replayed by httpx.MockTransport.
"""

from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

from bookworm.modules.catalogues import BookQuery, CatalogueGateway, HoldingStatus, SearchOutcome
from bookworm.modules.catalogues import registry as adapter_registry
from bookworm.shared.clients import open_clients
from bookworm.shared.config import Settings
from tests._adapters.fake import FakeMemoryAdapter
from tests._fixtures.records import make_catalogue

RECORDINGS = Path(__file__).parents[2] / "_recordings" / "fake_http"
QUERY = BookQuery(isbn="9781607322221")


def replay(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def recording(name: str) -> Callable[[httpx.Request], httpx.Response]:
    body = (RECORDINGS / name).read_bytes()
    return lambda request: httpx.Response(200, content=body, headers={"content-type": "application/json"})


async def search_with(settings: Settings, data_dir: Path, transport: httpx.MockTransport):  # type: ignore[no-untyped-def]
    catalogue = make_catalogue(data_dir, access=[{"adapter": "fake.http"}])
    async with open_clients(settings, transport=transport) as clients:
        return await CatalogueGateway(clients=clients).search(catalogue=catalogue, query=QUERY)


@pytest.mark.test_id("CAT-007")
async def test_a_recorded_response_is_mapped_to_canonical_records(settings: Settings, data_dir: Path) -> None:
    result = await search_with(settings, data_dir, replay(recording("search_two_branches.json")))

    assert result.outcome is SearchOutcome.answered
    (record,) = result.records
    assert record.isbns == ("9781607322221",)
    assert record.holdings is not None
    assert [(h.location_code, h.status) for h in record.holdings] == [
        ("CENTRAL", HoldingStatus.available),
        ("NORTH", HoldingStatus.on_loan),
    ]


@pytest.mark.test_id("CAT-007")
async def test_a_response_of_the_wrong_shape_is_catalogue_changed(settings: Settings, data_dir: Path) -> None:
    result = await search_with(settings, data_dir, replay(recording("search_changed_shape.json")))

    assert result.outcome is SearchOutcome.failed
    assert result.attempts[0].error == "CatalogueChangedError"


@pytest.mark.test_id("CAT-007")
@pytest.mark.parametrize(
    ("status", "error"),
    [
        (403, "CatalogueBlockedError"),
        (429, "CatalogueBlockedError"),
        (404, "CatalogueUnavailableError"),
        (503, "CatalogueUnavailableError"),
    ],
    ids=["forbidden", "too-many-requests", "not-found", "unavailable"],
)
async def test_http_errors_are_translated(
    settings: Settings, data_dir: Path, status: int, error: str
) -> None:
    result = await search_with(settings, data_dir, replay(lambda request: httpx.Response(status)))

    assert result.attempts[0].error == error


@pytest.mark.test_id("CAT-007")
async def test_a_timeout_is_catalogue_unavailable(settings: Settings, data_dir: Path) -> None:
    def time_out(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    result = await search_with(settings, data_dir, replay(time_out))

    assert result.attempts[0].error == "CatalogueUnavailableError"
    assert "timed out" in result.attempts[0].detail


@pytest.mark.test_id("CAT-009")
def test_the_registry_rejects_a_malformed_or_duplicate_id() -> None:
    class BadId(FakeMemoryAdapter):
        id = "no-dot"

    class Duplicate(FakeMemoryAdapter):
        id = "fake.memory"

    with pytest.raises(ValueError, match="expected '<system>.<method>'"):
        adapter_registry.register(BadId)
    with pytest.raises(ValueError, match="already registered"):
        adapter_registry.register(Duplicate)
