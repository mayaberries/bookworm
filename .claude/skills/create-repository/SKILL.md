---
name: create-repository
description: Create or change a repository in bookworm, the class that reads and writes one kind of stored thing (record files today; a results store later) and returns models. Use for "store lookup results", "add a list_by_kind to libraries", "records need a second folder", or when a service is reaching into files directly.
---

# Create a repository

Adapted from the `create-repository` skill shared by Vetted, Sinapsis, Kalens and Xolo. There, a repository runs SQL against its own table; here the "tables" are folders of record files (`data/libraries/`, `data/catalogues/`), and later perhaps a results store. The job is the same: **read and write its own stored thing, and return models.**

| Concern | Goes in | Not in the repository because |
|---|---|---|
| Rules spanning records ("a library's catalogue must exist") | service | they need other repositories |
| "Missing is an error" | service (`NotFoundError`) | the repository returns `None`; the caller decides |
| Filtering by a rule (`alcaldia`, `catalogue`) | service, unless it's a cheap lookup by key | keeps the repository a storage API |
| Talking to catalogues | adapters | a catalogue is not storage |
| Format parsing (YAML frontmatter) | `shared/frontmatter.py` | shared by every record repository |

The model to copy is `LibrariesRepository` (`src/bookworm/modules/directory/repository.py`).

## 1. Shape

```python
class CataloguesRepository:
    def __init__(self, data_dir: Path) -> None:
        self.files = _RecordFiles(data_dir / "catalogues")

    def load(self, path: Path) -> Catalogue: ...                 # raises InvalidRecordError naming file + field
    def get(self, *, slug: str) -> Catalogue | None: ...         # None when missing
    def list_all(self) -> list[Catalogue]: ...
    def list_paths(self) -> list[Path]: ...                      # for the record check, which reports per file
    def save(self, *, catalogue: Catalogue) -> Path: ...         # only if something writes them
```

- **Constructed with where it reads from** (`data_dir`), never reading settings itself. The module's `build_*_service(data_dir)` wires it.
- **Keyword-only arguments**, named for what they are (`slug=`).
- **Return the model, `X | None` or `list[X]`**, annotated exactly. Not found is `None`.
- **Translate storage failures at the boundary** into domain errors: an unparseable file or a `ValidationError` becomes `InvalidRecordError` with the path and the field (`_describe`). Nothing above sees a `yaml.YAMLError` or a raw `ValidationError` from a record.
- **Only its own folder.** No other repository inside it, no reading another kind's files. Anything that needs two is a service.
- **No caching** unless measured. Records are read on every call so an edit is seen at once. If it becomes slow, the cache goes inside the repository behind the same methods.
- **Writes go through the record model** (`XRecord(**x.model_dump(exclude=...))`) so a write can never produce a file the loader would reject; `exclude_defaults=True` keeps files short.

## 2. A new kind of storage

A results store (roadmap: Coverage) is an open decision; when it's made, its repository follows the same rules: constructed with its location, returns canonical or report models, `None` for missing, its own errors translated at the boundary, and the format choice recorded in `docs/DECISIONS.md`. If it's a database, its schema and migrations get their own decision first.

## 3. Test it

Against real files in the per-test `data_dir` fixture (`tests/_fixtures/settings.py`), built with the factories in `tests/_fixtures/records.py`. No mocks.

- happy path of each method; `None` for a missing slug;
- each kind of bad file → `InvalidRecordError` naming the file and the field;
- templates (`_*.md`) skipped;
- `save` then `get` returns an equal model.

## Checklist

- [ ] Constructed with its location; no settings read inside
- [ ] Returns `X`, `X | None`, `list[X]`; missing is `None`
- [ ] Storage errors translated to domain errors naming the file and field
- [ ] Only its own folder/store; cross-record rules in the service
- [ ] Writes go through the record model; round-trip tested
