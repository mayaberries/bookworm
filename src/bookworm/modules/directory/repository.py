"""
The directory's repositories: the record files are the tables.

Same job as a SQL repository in Kalens or Sinapsis (see the
`create-repository` skill): read and write *its own* records and return
models. No rules about other records (does a library's catalogue exist?),
which are the service's.

WHY FILES, READ EVERY TIME
    A few hundred small files parse in milliseconds, and reading them on each
    call means an edit in Obsidian is seen by the next command with no cache
    to invalidate. If that ever gets slow, a cache goes here, behind the same
    methods.
"""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bookworm.modules.directory.schemas import Catalogue, CatalogueRecord, Library, LibraryRecord
from bookworm.shared.errors import InvalidRecordError
from bookworm.shared.frontmatter import read_record, write_record

RECORD_SUFFIX = ".md"


def _describe(path: Path, exc: ValidationError) -> str:
    problems = "; ".join(
        f"{'.'.join(str(part) for part in error['loc']) or '(file)'}: {error['msg']}"
        for error in exc.errors()
    )
    return f"{path}: {problems}"


class _RecordFiles:
    """One folder of `<slug>.md` files. Files starting with `_` (templates)
    are skipped."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder

    def paths(self) -> list[Path]:
        if not self.folder.is_dir():
            return []
        return sorted(p for p in self.folder.glob(f"*{RECORD_SUFFIX}") if not p.name.startswith("_"))

    def path_for(self, slug: str) -> Path:
        return self.folder / f"{slug}{RECORD_SUFFIX}"

    def read(self, path: Path) -> tuple[dict[str, Any], str]:
        data, body = read_record(path)
        if "slug" in data:
            raise InvalidRecordError(f"{path}: 'slug' isn't a field; the file name is the slug")
        return data, body


class LibrariesRepository:
    def __init__(self, data_dir: Path) -> None:
        self.files = _RecordFiles(data_dir / "libraries")

    def load(self, path: Path) -> Library:
        data, body = self.files.read(path)
        try:
            return Library(**LibraryRecord(**data).model_dump(), slug=path.stem, notes=body)
        except ValidationError as exc:
            raise InvalidRecordError(_describe(path, exc)) from exc

    def get(self, *, slug: str) -> Library | None:
        path = self.files.path_for(slug)
        return self.load(path) if path.is_file() else None

    def list_all(self) -> list[Library]:
        return [self.load(path) for path in self.files.paths()]

    def list_paths(self) -> list[Path]:
        return self.files.paths()

    def save(self, *, library: Library) -> Path:
        path = self.files.path_for(library.slug)
        record = LibraryRecord(**library.model_dump(exclude={"slug", "notes"}))
        write_record(path, record.model_dump(mode="json", exclude_defaults=True), library.notes)
        return path


class CataloguesRepository:
    def __init__(self, data_dir: Path) -> None:
        self.files = _RecordFiles(data_dir / "catalogues")

    def load(self, path: Path) -> Catalogue:
        data, body = self.files.read(path)
        try:
            return Catalogue(**CatalogueRecord(**data).model_dump(), slug=path.stem, notes=body)
        except ValidationError as exc:
            raise InvalidRecordError(_describe(path, exc)) from exc

    def get(self, *, slug: str) -> Catalogue | None:
        path = self.files.path_for(slug)
        return self.load(path) if path.is_file() else None

    def list_all(self) -> list[Catalogue]:
        return [self.load(path) for path in self.files.paths()]

    def list_paths(self) -> list[Path]:
        return self.files.paths()
