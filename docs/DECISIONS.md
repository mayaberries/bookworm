# 🧭 Bookworm: decisions

← [Roadmap](ROADMAP.md)

> Look here first when you need to know why bookworm is built the way it is: the principles every stage follows and the decisions already made. Decisions still open live in each [stage](stages/) file and in the roadmap; once made, they're recorded here.

## 📐 Principles

- **Records drive behaviour.** Supporting a library is a record; supporting a library whose catalogue runs software we already support is a record too. Code is only for a new kind of catalogue.
- **Never ask a catalogue that hasn't said yes.** Bookworm sends requests only to catalogues whose record says `automation: allowed`, set by a person after reading its robots.txt and terms. `unknown` counts as no. Requests are paced per catalogue.
- **Partial answers beat no answer.** One catalogue failing never fails a lookup; its libraries say "search failed" and the rest answer.
- **Say how sure we are.** Records carry their verification status, date and source; results say whether a match is exact (ISBN) or possible, and keep the catalogue's own words for a copy's status.
- **Prove it offline.** The suite never touches the network: records are temporary files, catalogues are reference adapters or recorded responses. Only `make test-live` talks to real catalogues.

## 🛠️ Technical decisions

Newest first. Each one says when it was made, what was decided, why, and what it implies.

### Catalogue adapters: ports and adapters behind one gateway

*Foundation · 2026-11-09*

**Decision**

- **One port, many adapters.** `Adapter` (`modules/catalogues/port.py`) has one operation, `search(BookQuery) -> list[BibRecord]`. Each way of talking to a kind of catalogue is one subclass with an id `<system>.<method>` (`vufind.api`, `vufind.html`, `vasconcelos.browser`), registered explicitly in `adapters/__init__.py`.
- **A catalogue's record lists its access methods in order** (`access:`), with per-catalogue `options` validated by the adapter's own `Options` model. The **gateway** tries them in order and falls through on any `CatalogueError`: an API that's off falls back to HTML, HTML that changed falls back to a browser.
- **Canonical models are the anti-corruption layer.** Adapters turn whatever they got (JSON, HTML, MARC) into `BibRecord` / `Holding` at the boundary, through `Raw*` models and pure `mapping.py` functions that never leave the adapter's package. Nothing past the gateway knows how a catalogue answered.
- **Adapters only touch `AdapterContext`**: the record, their options, and the paced, error-translating `get()` / `page()`. HTTP and browser clients are opened once per lookup and shared; Chromium only starts if an adapter asks for a page.
- **Failures are values past the gateway**: `CatalogueSearch.outcome` is `answered`, `no_access`, `not_allowed` or `failed`, with every attempt recorded. Bugs (anything not a `CatalogueError`) still raise.
- **The lookup searches per catalogue, not per library**, and gives each library its share by `catalogue_location`.

**Why**

- The same catalogue software is reachable in several ways (VuFind's REST API is optional per install; its HTML always works), and the same way works for many installs. Keying adapters by system and method, and configuring installs in records, makes a new VuFind library a record and nothing else.
- Catalogues change without notice. A typed error per kind of failure (`Changed`, `Blocked`, `Unavailable`) tells the next person whether to fix the adapter, slow down, or wait.
- UNAM's Descubridor answers for dozens of libraries; searching it once per library would multiply the load on it for nothing.

**Implies**

- Adding an adapter: the `create-adapter` skill. Adding a catalogue or library: `add-catalogue`, `add-library`.
- Adapters are tested against recorded responses (`tests/_recordings/`) through `httpx.MockTransport`, plus one `live` test each.
- The suite's reference adapters (`tests/_adapters/fake.py`) are real implementations of the port, as Kalens' and Xolo's `tests/_host/` are real hosts.

### Records are Markdown files with YAML frontmatter

*Foundation · 2026-11-09*

**Decision**

- **One file per record**: `data/libraries/<slug>.md` and `data/catalogues/<slug>.md`. The file name is the slug; the frontmatter is the record; the Markdown body is free notes.
- **Two kinds of record**: a *catalogue* is software at a URL; a *library* is a building that points at the catalogue that lists its books (`catalogue`), plus how that catalogue names it (`catalogue_location`). A library with no online catalogue has `catalogue: null`.
- The frontmatter is validated by `LibraryRecord` / `CatalogueRecord` (`extra="forbid"`); `make check-records` validates the whole folder, the slugs records name, and each catalogue's access methods. It runs in `make verify` and CI.
- Files starting with `_` are templates and are skipped.

**Why**

- A record has two readers: code reads the fields, people read the notes (how the catalogue behaves, what was tried). One file keeps them reviewed together, in git, with readable diffs.
- Markdown with frontmatter opens as an Obsidian vault with the fields as properties, the way Sinapsis' and Xolo's docs are kept.
- A database would add a server and migrations for a few hundred rows that change by hand. Files keep "add a library" a pull request.
- Catalogues and libraries are many-to-one (UNAM) and zero-to-one (alcaldía branches), so one record type couldn't hold both without duplicating catalogue data in every UNAM library.

**Implies**

- The repositories (`modules/directory/repository.py`) read files on every call; there's no cache to invalidate. If that gets slow, a cache goes behind the same methods.
- Changing a record model's field is a change to every file: rename in one PR with all files updated, and `check-records` green.

### Python, modules first, layers enforced

*Foundation · 2026-11-09*

**Decision**

- **Python 3.13 with uv**, every dependency pinned exactly in `pyproject.toml` (Kalens' and Xolo's rule: versions move deliberately, with the suite green). Pydantic for every model, httpx for HTTP, Playwright for browsers, Typer for the CLI.
- **Sinapsis' structure: modules first, layers inside.** `modules/directory/` (records), `modules/catalogues/` (the unified API over catalogues), `modules/lookup/` (the use case). Layers are files, in one direction: `service → gateway → adapters → registry → repository → port → schemas`, each optional. Modules use each other only through their package's `__init__`. `shared/` (config, errors, model bases, clients, frontmatter) imports no module.
- **The CLI is the only entry point** (the routes of the API projects): it parses into an input model, calls one service method, renders, and maps domain errors to exit codes in one place.
- `make lint` enforces the layering with import-linter, and Ruff; `make typecheck` runs mypy `--strict`.
- **Workflow:** Sinapsis' and Xolo's stages, stories, tasks, boards and test IDs, with their `create-story`, `create-task` and `close-ticket` skills adapted. The architecture skills (`create-model`, `create-repository`, `create-service`, `add-setting`, `write-tests`) are adapted from the ones shared by Vetted, Sinapsis, Kalens and Xolo, without HTTP or SQL.

**Why**

- The user's other projects are Python, and so is Playwright's best-maintained binding outside Node.
- The same structure and vocabulary across repos means the same skills and habits apply; import-linter makes the rules checkable rather than remembered.
- There's no API here, so the rules that came from FastAPI (status codes, dependencies, OpenAPI) are replaced by their CLI equivalents rather than dropped.

**Implies**

- New domains are new packages in `modules/`; a module that needs another's internals has a misplaced boundary.
- Settings are the app's (`BOOKWORM_*` environment variables); anything about one catalogue is in its record, never in settings.
