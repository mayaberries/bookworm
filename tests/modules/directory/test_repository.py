from pathlib import Path

import pytest

from bookworm.modules.directory import Alcaldia, Library
from bookworm.modules.directory.repository import LibrariesRepository
from bookworm.shared.errors import InvalidRecordError
from bookworm.shared.frontmatter import write_record
from tests._fixtures.records import make_library


@pytest.mark.test_id("DIR-001")
def test_a_record_file_loads_with_its_file_name_as_slug_and_its_body_as_notes(data_dir: Path) -> None:
    make_library(data_dir, slug="biblioteca-x", alcaldia="Coyoacán", notes="Opens at 9.")

    library = LibrariesRepository(data_dir).get(slug="biblioteca-x")

    assert isinstance(library, Library)
    assert library.slug == "biblioteca-x"
    assert library.alcaldia is Alcaldia.coyoacan
    assert library.notes == "Opens at 9."


@pytest.mark.test_id("DIR-001")
def test_a_missing_slug_is_none(data_dir: Path) -> None:
    assert LibrariesRepository(data_dir).get(slug="nowhere") is None


@pytest.mark.test_id("DIR-002")
def test_an_unknown_field_is_rejected_naming_the_file_and_field(data_dir: Path) -> None:
    path = data_dir / "libraries" / "typo.md"
    write_record(path, {"name": "Typo", "kind": "public", "alcadia": "Coyoacán"})

    with pytest.raises(InvalidRecordError) as exc:
        LibrariesRepository(data_dir).load(path)

    assert str(path) in exc.value.detail
    assert "alcadia" in exc.value.detail


@pytest.mark.test_id("DIR-002")
def test_an_invalid_value_is_rejected_naming_the_field(data_dir: Path) -> None:
    path = data_dir / "libraries" / "bad-kind.md"
    write_record(path, {"name": "Bad", "kind": "bookshop"})

    with pytest.raises(InvalidRecordError, match="kind"):
        LibrariesRepository(data_dir).load(path)


@pytest.mark.test_id("DIR-003")
def test_slug_in_the_frontmatter_is_rejected(data_dir: Path) -> None:
    # The file name is the slug; a second source of truth would drift.
    path = data_dir / "libraries" / "a.md"
    write_record(path, {"slug": "b", "name": "A", "kind": "public"})

    with pytest.raises(InvalidRecordError, match="file name is the slug"):
        LibrariesRepository(data_dir).load(path)


@pytest.mark.test_id("DIR-004")
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("name: A\n", "must start with a '---'"),
        ("---\nname: A\n", "no closing '---'"),
        ("---\nname: [unclosed\n---\n", "isn't valid YAML"),
        ("---\n- a list\n---\n", "mapping of fields"),
    ],
    ids=["no-opening", "no-closing", "bad-yaml", "not-a-mapping"],
)
def test_a_malformed_file_is_rejected_saying_why(data_dir: Path, text: str, expected: str) -> None:
    path = data_dir / "libraries" / "broken.md"
    path.write_text(text)

    with pytest.raises(InvalidRecordError, match=expected):
        LibrariesRepository(data_dir).load(path)


@pytest.mark.test_id("DIR-005")
def test_files_starting_with_underscore_are_templates_and_skipped(data_dir: Path) -> None:
    (data_dir / "libraries" / "_template.md").write_text("not even frontmatter")
    real = make_library(data_dir)

    assert [lib.slug for lib in LibrariesRepository(data_dir).list_all()] == [real.slug]


@pytest.mark.test_id("DIR-008")
def test_save_writes_a_file_that_loads_back_the_same(data_dir: Path) -> None:
    repo = LibrariesRepository(data_dir)
    library = Library(
        slug="round-trip", name="Round Trip", kind="academic", alcaldia="Tlalpan", notes="Body."
    )

    repo.save(library=library)

    assert repo.get(slug="round-trip") == library
