# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Bookworm answers "is this book at that library?" for Mexico City, where no single catalogue covers every library. It keeps a **record** for every library and every **catalogue** (the software that lists a library's books), and searches catalogues through **adapters**: REST APIs, HTML pages or a headless browser, depending on how each catalogue is exposed. The README describes the problem and the library landscape.

**State:** the Foundation stage is built (records, adapter port, gateway, lookup, CLI, harness), proven with reference adapters only. No real catalogue adapter exists yet; the seed records come from the README's landscape table. The work is tracked as documented in `docs/`:

- `docs/ROADMAP.md`: the four stages (Foundation → Census → First catalogues → Coverage) and cross-stage open decisions.
- `docs/stages/NN-*.md`: per stage: what it demonstrates, exit criteria, its stories (each tagged with its board), story notes, open decisions and decisions made.
- `docs/DECISIONS.md`: why things are built the way they are. When an open decision is made, record it here and in its stage's "Decisions made".
- `docs/boards/`: one file per board (PLT, DIR, MAP, CAT, LKP), indexed in `docs/boards/README.md`. The board prefix is also the test ID prefix (`XXX-NNN`).
- `docs/WORKFLOW.md`: vocabulary, the GitHub mapping and the test-driven cycle. Adapted from `../sinapsis` and `../xolo`; keep them compatible.

There's no GitHub repo yet (a roadmap open decision), so stories have no issues; the `create-story`, `create-task` and `close-ticket` skills say what to do without one.

## Commands

Python 3.13 with uv; every dependency is pinned exactly in `pyproject.toml` (move versions deliberately, with the suite green).

- `make install`: `.venv` with bookworm (editable) and the dev tools (`uv sync`).
- `make browsers`: download Chromium for Playwright. Only browser adapters need it.
- `make test`: the offline suite. `make test ID=CAT-004` (or `ID="CAT-004 LKP-002"`) runs only those test cases; directly, `uv run pytest --test-id CAT-004`. One file: `uv run pytest tests/modules/lookup/test_service.py`.
- `make test-live`: only the `live` tests, which talk to real catalogues. Never in CI.
- `make lint`: Ruff (check and format) and import-linter (the layering rules below). `make format` applies fixes.
- `make typecheck`: mypy `--strict` on `src`.
- `make check-records`: validate every file in `data/` (`uv run bookworm records check`).
- `make verify`: lint + typecheck + test + check-records. CI (`.github/workflows/ci.yml`) runs it on every PR and push to `main`.

The CLI: `uv run bookworm find --isbn … [--library <slug> …] [--json]`, `bookworm libraries list [--alcaldia …] [--catalogue …]`, `bookworm libraries show <slug>`, `bookworm records check`. Settings are `BOOKWORM_*` environment variables (`src/bookworm/shared/config.py`), e.g. `BOOKWORM_DATA_DIR`.

## Architecture

Sinapsis' structure: **modules first, layers inside**, enforced by import-linter in `make lint`.

```
src/bookworm/
  cli.py                     # the only entry point: parse → one service call → render; errors → exit codes
  modules/
    directory/               # records: libraries and catalogues (data/*.md)
      __init__.py            # public API + build_directory_service(data_dir)
      service.py → repository.py → schemas.py
    catalogues/              # the unified internal API over every catalogue
      __init__.py            # public API: CatalogueGateway, canonical models, Adapter, register
      gateway.py → adapters/ → registry.py → port.py → schemas.py
    lookup/                  # "is this book at these libraries?"
      __init__.py            # public API + open_lookup_service(settings)
      service.py → schemas.py
  shared/                    # config, errors, model bases, clients (http/browser), frontmatter
data/libraries/<slug>.md     # one library per file
data/catalogues/<slug>.md    # one catalogue per file
```

- **Layers are files, in one direction**, each optional: `service → gateway → adapters → registry → repository → port → schemas`.
- **Modules use each other only through their package** (`from bookworm.modules.directory import Library`), never another module's files. `lookup` → `catalogues` → `directory`.
- **`shared/` never imports a module or the CLI**; nothing imports the CLI.

### Records (the data model)

A record is a Markdown file: YAML frontmatter (validated by `LibraryRecord` / `CatalogueRecord`, unknown keys are errors) and free notes as the body. **The file name is the slug.** Files starting with `_` are templates. A *catalogue* is software at a URL; a *library* points at the catalogue that lists its books (`catalogue`, or `null`) and says how that catalogue names it (`catalogue_location`), so libraries sharing a catalogue (UNAM) are answered by one search. The repositories read files on every call; there is no cache.

### Catalogues: ports and adapters

- `Adapter` (`port.py`) is the port: `search(BookQuery) -> list[BibRecord]`. Each way of talking to a kind of catalogue is a subclass with an id `<system>.<method>` (`vufind.api`), registered with `@register` and imported explicitly in `adapters/__init__.py`.
- A catalogue's record lists `access` methods in order, with per-catalogue `options` validated by the adapter's `Options` model. The **gateway** tries them in order and falls through on any `CatalogueError`.
- Adapters only touch `AdapterContext`: the record, their options, and `get()` / `page()`, which pace requests per catalogue (`min_seconds_between_requests`) and translate httpx/Playwright failures into `CatalogueUnavailableError` / `CatalogueBlockedError`. Raw source shapes are `Raw*` models mapped to canonical `BibRecord` / `Holding` by pure functions in the adapter's package; nothing past the gateway sees them.
- Clients are opened once per lookup (`shared/clients.py`); Chromium starts only if an adapter asks for a page.

### Errors

`shared/errors.py`: `DomainError` → `NotFoundError`, `InvalidRecordError`, and `CatalogueError` → `CatalogueUnavailableError`, `CatalogueBlockedError`, `CatalogueChangedError`, `UnsupportedQueryError`. Repositories and adapters translate library exceptions at the boundary. Past the gateway, catalogue failures are **values** (`CatalogueSearch.outcome`, `LibraryOutcome.failed`), so one catalogue never fails a lookup. The CLI maps the rest to exit codes in `EXIT_CODES` (2 bad input, 3 not found, 4 invalid records).

## Behaviour that looks like a bug but isn't

- **Catalogues with `automation: unknown` are never queried**, only `allowed` ones. `make check-records` refuses access methods on a catalogue that isn't `allowed` with a `robots_checked_on` date. Biblioteca de México is `disallowed` because its robots.txt blocks automated access.
- A lookup reports "check by hand" for libraries with no catalogue, a disallowed catalogue, or no adapter yet. That's an answer, not a failure.
- A title/author search marks every match `possible`; only an ISBN listed in the record is `exact`.
- `holdings=None` (the adapter didn't fetch copies) and `holdings=()` (no copies) are different, and give different outcomes.

## Skills

Use the project skills for these, so code, records and docs stay consistent:

- Workflow: `create-story`, `create-task`, `close-ticket`.
- Records: `add-library`, `add-catalogue`.
- Code: `create-adapter` (a new catalogue system or access method), `create-model`, `create-repository`, `create-service`, `create-command`, `add-setting`, `write-tests`.

The code skills are adapted from the ones shared by Vetted (`../pets-appts`), `../sinapsis`, `../kalens` and `../xolo`, without HTTP or SQL. They are not identical copies; don't sync them back.

## Tests

- Offline by default: each test gets its own empty `data/` (`data_dir`, `settings` fixtures in `tests/_fixtures/`), records come from the factories in `tests/_fixtures/records.py`, catalogues from the reference adapters in `tests/_adapters/fake.py` (registered per test) or recordings in `tests/_recordings/` replayed with `httpx.MockTransport`. No mocks of our own code.
- Mark each test with the case it proves: `@pytest.mark.test_id("CAT-004")`. IDs that aren't `XXX-NNN` stop the run (`tests/_plugins/test_ids.py`, from Xolo). `--strict-markers` rejects undeclared markers; the declared ones are `test_id` and `live`.
- PLT-002 validates the committed `data/`, so an invalid record fails the suite.

## Conventions

- Module and class docstrings explain *why*, often under capitalised headings (`WHY TWO KINDS OF RECORD`), as in Kalens and Xolo. Keep them when refactoring and match their style.
- Never fill a record field from a guess: leave it `null` and say so in the notes. Every record names its source and date in `verification`.
- The HTTP User-Agent identifies bookworm generically; never put a person's name or email in it.
- Don't commit unless asked. This repo has no local git identity yet; per the sibling repos, set it with `git config --local`, never `--global`.
