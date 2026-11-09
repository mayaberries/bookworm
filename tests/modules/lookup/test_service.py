from pathlib import Path
from typing import Any

import pytest

from bookworm.modules.catalogues import BookQuery
from bookworm.modules.lookup import AvailabilityReport, LibraryOutcome, Match, open_lookup_service
from bookworm.shared.config import Settings
from tests._adapters.fake import FakeMemoryAdapter
from tests._fixtures.records import fake_record, make_catalogue, make_library

ISBN = "9781607322221"


def memory(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"adapter": "fake.memory", "options": {"records": records}}]


def copy(location: str, status: str) -> dict[str, str]:
    return {"location_code": location, "status": status}


async def find(settings: Settings, **kwargs: Any) -> AvailabilityReport:
    async with open_lookup_service(settings) as service:
        return await service.find(**kwargs)


def outcomes(report: AvailabilityReport) -> dict[str, LibraryOutcome]:
    return {r.library: r.outcome for r in report.results}


@pytest.mark.test_id("LKP-001")
async def test_libraries_sharing_a_catalogue_cost_one_search(settings: Settings, data_dir: Path) -> None:
    unam = make_catalogue(data_dir, access=memory([]))
    make_library(data_dir, catalogue=unam.slug, catalogue_location="A")
    make_library(data_dir, catalogue=unam.slug, catalogue_location="B")
    make_library(data_dir, catalogue=unam.slug, catalogue_location="C")

    report = await find(settings, query=BookQuery(isbn=ISBN))

    assert len(report.results) == 3
    assert [slug for slug, _ in FakeMemoryAdapter.searches] == [unam.slug]


@pytest.mark.test_id("LKP-002")
async def test_each_library_sees_only_its_own_copies(settings: Settings, data_dir: Path) -> None:
    record = fake_record(isbns=[ISBN], holdings=[copy("CENTRAL", "available"), copy("NORTH", "on_loan")])
    shared = make_catalogue(data_dir, access=memory([record]))
    central = make_library(data_dir, catalogue=shared.slug, catalogue_location="CENTRAL")
    north = make_library(data_dir, catalogue=shared.slug, catalogue_location="NORTH")
    south = make_library(data_dir, catalogue=shared.slug, catalogue_location="SOUTH")

    report = await find(settings, query=BookQuery(isbn=ISBN))

    assert outcomes(report) == {
        central.slug: LibraryOutcome.available,
        north.slug: LibraryOutcome.held_not_available,
        south.slug: LibraryOutcome.not_found,
    }


@pytest.mark.test_id("LKP-003")
async def test_libraries_we_cant_search_say_to_check_by_hand(settings: Settings, data_dir: Path) -> None:
    disallowed = make_catalogue(data_dir, automation="disallowed", access=memory([]))
    no_adapter = make_catalogue(data_dir, access=[])
    branch = make_library(data_dir)  # no online catalogue
    robots = make_library(data_dir, catalogue=disallowed.slug)
    pending = make_library(data_dir, catalogue=no_adapter.slug)

    report = await find(settings, query=BookQuery(title="Aztec Philosophy"))

    assert set(outcomes(report).values()) == {LibraryOutcome.check_manually}
    details = {r.library: r.detail for r in report.results}
    assert "call or visit" in (details[branch.slug] or "")
    assert "doesn't allow automated" in (details[robots.slug] or "")
    assert "can't search its catalogue yet" in (details[pending.slug] or "")
    assert FakeMemoryAdapter.searches == []


@pytest.mark.test_id("LKP-004")
async def test_isbn_matches_are_exact_only_when_the_record_lists_it(
    settings: Settings, data_dir: Path
) -> None:
    listed = fake_record(record_id="listed", isbns=[ISBN])
    unlisted = fake_record(record_id="unlisted")
    catalogue = make_catalogue(data_dir, access=memory([listed, unlisted]))
    library = make_library(data_dir, catalogue=catalogue.slug)

    report = await find(settings, query=BookQuery(isbn="1-60732-222-X"), library_slugs=[library.slug])

    (result,) = report.results
    assert {f.record.record_id: f.match for f in result.found} == {
        "listed": Match.exact,
        "unlisted": Match.possible,
    }


@pytest.mark.test_id("LKP-005")
@pytest.mark.parametrize(
    ("records", "expected"),
    [
        ([], LibraryOutcome.not_found),
        ([fake_record()], LibraryOutcome.held_status_unknown),  # copies not listed
        ([fake_record(holdings=[copy("X", "unknown")])], LibraryOutcome.held_status_unknown),
        (
            [fake_record(holdings=[copy("X", "on_loan"), copy("X", "on_site_only")])],
            LibraryOutcome.held_not_available,
        ),
        ([fake_record(holdings=[])], LibraryOutcome.not_found),  # listed copies: none
    ],
    ids=["no-records", "holdings-not-fetched", "status-unmapped", "none-on-shelf", "no-copies"],
)
async def test_outcome_from_what_the_catalogue_said(
    settings: Settings, data_dir: Path, records: list[dict[str, Any]], expected: LibraryOutcome
) -> None:
    catalogue = make_catalogue(data_dir, access=memory(records))
    library = make_library(data_dir, catalogue=catalogue.slug, catalogue_location="X")

    report = await find(settings, query=BookQuery(title="A Book"), library_slugs=[library.slug])

    assert outcomes(report) == {library.slug: expected}


@pytest.mark.test_id("LKP-006")
async def test_a_failing_catalogue_fails_only_its_libraries(settings: Settings, data_dir: Path) -> None:
    broken = make_catalogue(
        data_dir, access=[{"adapter": "fake.memory", "options": {"fail_with": "CatalogueBlockedError"}}]
    )
    working = make_catalogue(data_dir, access=memory([fake_record(holdings=[copy("X", "available")])]))
    a = make_library(data_dir, catalogue=broken.slug)
    b = make_library(data_dir, catalogue=working.slug)

    report = await find(settings, query=BookQuery(title="A Book"))

    assert outcomes(report) == {a.slug: LibraryOutcome.failed, b.slug: LibraryOutcome.available}
    failed = next(r for r in report.results if r.library == a.slug)
    assert "CatalogueBlockedError" in (failed.detail or "")
