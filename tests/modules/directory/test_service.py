from pathlib import Path

import pytest

from bookworm.modules.directory import Alcaldia, build_directory_service
from bookworm.shared.errors import NotFoundError
from bookworm.shared.frontmatter import write_record
from tests._fixtures.records import make_catalogue, make_library


@pytest.mark.test_id("DIR-006")
def test_check_records_reports_every_problem_not_just_the_first(data_dir: Path) -> None:
    make_library(
        data_dir, slug="points-nowhere", catalogue="ghost-catalogue", interlibrary_loan=["ghost-library"]
    )
    write_record(data_dir / "libraries" / "unparseable.md", {"name": "X"})  # no kind
    write_record(data_dir / "catalogues" / "no-url.md", {"name": "Y"})  # no base_url

    issues = build_directory_service(data_dir).check_records()

    details = sorted(f"{Path(i.path).name}: {i.detail}" for i in issues)
    assert len(details) == 4
    assert any(d.startswith("no-url.md") and "base_url" in d for d in details)
    assert any(d.startswith("unparseable.md") and "kind" in d for d in details)
    assert "points-nowhere.md: catalogue: no catalogue 'ghost-catalogue'" in details
    assert "points-nowhere.md: interlibrary_loan: no library 'ghost-library'" in details


@pytest.mark.test_id("DIR-006")
def test_check_records_is_empty_for_consistent_records(data_dir: Path) -> None:
    catalogue = make_catalogue(data_dir)
    partner = make_library(data_dir)
    make_library(data_dir, catalogue=catalogue.slug, interlibrary_loan=[partner.slug])

    assert build_directory_service(data_dir).check_records() == []


@pytest.mark.test_id("DIR-007")
def test_a_missing_library_is_not_found(data_dir: Path) -> None:
    with pytest.raises(NotFoundError, match="nowhere"):
        build_directory_service(data_dir).get_library(slug="nowhere")


@pytest.mark.test_id("DIR-007")
def test_libraries_filter_by_alcaldia_and_catalogue(data_dir: Path) -> None:
    unam = make_catalogue(data_dir)
    in_coyoacan = make_library(data_dir, alcaldia="Coyoacán", catalogue=unam.slug)
    make_library(data_dir, alcaldia="Tlalpan", catalogue=unam.slug)
    make_library(data_dir, alcaldia="Coyoacán")
    service = build_directory_service(data_dir)

    result = service.list_libraries(alcaldia=Alcaldia.coyoacan, catalogue=unam.slug)

    assert [lib.slug for lib in result] == [in_coyoacan.slug]
