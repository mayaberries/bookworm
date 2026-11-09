from pathlib import Path

import pytest

from bookworm.modules.catalogues import BookQuery, CatalogueGateway, SearchOutcome, check_access
from bookworm.shared.clients import open_clients
from bookworm.shared.config import Settings
from tests._adapters.fake import FakeMemoryAdapter
from tests._fixtures.records import fake_record, make_catalogue

ISBN_QUERY = BookQuery(isbn="9781607322221")


@pytest.mark.test_id("CAT-002")
@pytest.mark.parametrize("automation", ["disallowed", "unknown"])
async def test_a_catalogue_not_marked_allowed_is_never_queried(
    settings: Settings, data_dir: Path, automation: str
) -> None:
    catalogue = make_catalogue(
        data_dir, automation=automation, access=[{"adapter": "fake.memory", "options": {"records": []}}]
    )

    async with open_clients(settings) as clients:
        result = await CatalogueGateway(clients=clients).search(catalogue=catalogue, query=ISBN_QUERY)

    assert result.outcome is SearchOutcome.not_allowed
    assert FakeMemoryAdapter.searches == []


@pytest.mark.test_id("CAT-003")
async def test_a_catalogue_without_access_methods_is_no_access(settings: Settings, data_dir: Path) -> None:
    catalogue = make_catalogue(data_dir, access=[])

    async with open_clients(settings) as clients:
        result = await CatalogueGateway(clients=clients).search(catalogue=catalogue, query=ISBN_QUERY)

    assert result.outcome is SearchOutcome.no_access


@pytest.mark.test_id("CAT-004")
async def test_a_failing_method_falls_through_to_the_next(settings: Settings, data_dir: Path) -> None:
    record = fake_record(title="Aztec Philosophy")
    catalogue = make_catalogue(
        data_dir,
        access=[
            {"adapter": "fake.memory", "options": {"fail_with": "CatalogueChangedError"}},
            {"adapter": "fake.memory", "options": {"records": [record]}},
        ],
    )

    async with open_clients(settings) as clients:
        result = await CatalogueGateway(clients=clients).search(catalogue=catalogue, query=ISBN_QUERY)

    assert result.outcome is SearchOutcome.answered
    assert result.answered_by == "fake.memory"
    assert [r.title for r in result.records] == ["Aztec Philosophy"]
    assert [(a.adapter, a.error) for a in result.attempts] == [("fake.memory", "CatalogueChangedError")]


@pytest.mark.test_id("CAT-005")
async def test_unknown_unsupported_and_misconfigured_methods_are_skipped(
    settings: Settings, data_dir: Path
) -> None:
    catalogue = make_catalogue(
        data_dir,
        access=[
            {"adapter": "nobody.wrote_this"},
            {"adapter": "fake.isbn_only", "options": {"records": []}},
            {"adapter": "fake.memory", "options": {"recrods": []}},
            {"adapter": "fake.memory", "options": {"records": []}},
        ],
    )

    async with open_clients(settings) as clients:
        result = await CatalogueGateway(clients=clients).search(
            catalogue=catalogue, query=BookQuery(title="X")
        )

    assert result.outcome is SearchOutcome.answered
    assert result.records == ()  # answered "nothing found", which is not a failure
    assert [(a.adapter, a.error) for a in result.attempts] == [
        ("nobody.wrote_this", "NotFoundError"),
        ("fake.isbn_only", "UnsupportedQueryError"),
        ("fake.memory", "InvalidOptions"),
    ]


@pytest.mark.test_id("CAT-006")
async def test_when_every_method_fails_the_search_failed(settings: Settings, data_dir: Path) -> None:
    catalogue = make_catalogue(
        data_dir,
        access=[
            {"adapter": "fake.memory", "options": {"fail_with": "CatalogueBlockedError"}},
            {"adapter": "fake.memory", "options": {"fail_with": "CatalogueUnavailableError"}},
        ],
    )

    async with open_clients(settings) as clients:
        result = await CatalogueGateway(clients=clients).search(catalogue=catalogue, query=ISBN_QUERY)

    assert result.outcome is SearchOutcome.failed
    assert [a.error for a in result.attempts] == ["CatalogueBlockedError", "CatalogueUnavailableError"]


@pytest.mark.test_id("CAT-008")
def test_check_access_flags_unregistered_adapters_and_bad_options(data_dir: Path) -> None:
    good = make_catalogue(data_dir, access=[{"adapter": "fake.memory", "options": {"records": []}}])
    bad = make_catalogue(
        data_dir,
        slug="bad",
        access=[{"adapter": "nobody.wrote_this"}, {"adapter": "fake.memory", "options": {"recrods": []}}],
    )

    unchecked = make_catalogue(
        data_dir,
        slug="unchecked",
        automation="unknown",
        robots_checked_on=None,
        access=[{"adapter": "fake.memory", "options": {"records": []}}],
    )

    issues = check_access([good, bad, unchecked])

    assert [(i.path, i.detail.split(":")[0]) for i in issues] == [
        ("data/catalogues/bad.md", "access.0.adapter"),
        ("data/catalogues/bad.md", "access.1.options"),
        ("data/catalogues/unchecked.md", "access"),
    ]
