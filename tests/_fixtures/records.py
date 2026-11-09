"""
Factories for record files. Plain functions, not fixtures: a test calls them
for exactly the records it needs, so its setup is visible in the test.

Each one writes a real file through the same `write_record` the app uses and
reads it back through the repository, so a factory can't build a record the
loader would reject. Slugs are unique by default; times are never random.
"""

from pathlib import Path
from typing import Any
from uuid import uuid4

from bookworm.modules.directory import Catalogue, Library
from bookworm.modules.directory.repository import CataloguesRepository, LibrariesRepository
from bookworm.shared.frontmatter import write_record


def _suffix() -> str:
    return uuid4().hex[:8]


def make_catalogue(data_dir: Path, *, slug: str | None = None, notes: str = "", **fields: Any) -> Catalogue:
    slug = slug or f"catalogue-{_suffix()}"
    values: dict[str, Any] = {
        "name": f"Catalogue {slug}",
        "base_url": f"https://{slug}.example.test",
        "automation": "allowed",
        "robots_checked_on": "2026-11-09",
        "min_seconds_between_requests": 0,
        **fields,
    }
    path = data_dir / "catalogues" / f"{slug}.md"
    write_record(path, values, notes)
    return CataloguesRepository(data_dir).load(path)


def make_library(data_dir: Path, *, slug: str | None = None, notes: str = "", **fields: Any) -> Library:
    slug = slug or f"library-{_suffix()}"
    values: dict[str, Any] = {"name": f"Library {slug}", "kind": "public", **fields}
    path = data_dir / "libraries" / f"{slug}.md"
    write_record(path, values, notes)
    return LibrariesRepository(data_dir).load(path)


def fake_record(**fields: Any) -> dict[str, Any]:
    """A canonical BibRecord as the `fake.memory` adapter's options take it."""
    return {"record_id": f"rec-{_suffix()}", "title": "A Book", **fields}
