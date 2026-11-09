---
name: write-tests
description: Write bookworm tests (pytest) for models, record repositories, services, the gateway, adapters (recorded responses and live tests) and CLI commands, with the right isolation, fixtures and test IDs. Use when adding or changing tests, or when another skill's "Test it" step applies.
---

# Write tests

Adapted from the `write-tests` skill shared by Vetted, Sinapsis, Kalens and Xolo. Their rule is "real app, real PostgreSQL, each test sees only its own data". Bookworm's version: **real code, real files, no network; each test sees only its own records.** No mocks of our own code.

## 1. Which test, for which layer

| Layer | Test | Uses | Where |
|---|---|---|---|
| **Model** | constraints at their edges, validators both ways, unknown fields rejected | nothing | `tests/modules/<m>/test_schemas.py` |
| **Repository** | each method, `None` for missing, each bad file → `InvalidRecordError` naming file and field | `data_dir` + factories | `test_repository.py` |
| **Service** | each rule and outcome, batching, failure isolation | `data_dir`, factories, reference adapters | `test_service.py` |
| **Gateway / port** | fall-through, skips, `not_allowed`, error translation | reference adapters, `httpx.MockTransport` | `tests/modules/catalogues/` |
| **Adapter mapping** | each recording and status entry → canonical | recordings, no I/O | `tests/modules/catalogues/adapters/<system>/` |
| **Adapter** | the request it sends, what it returns, `CatalogueChangedError` on a wrong shape | recordings via `MockTransport` | same |
| **Adapter, live** | the real catalogue answers a known book | the network, `@pytest.mark.live` | same |
| **Command** | exit codes, `--json` parses | `CliRunner`, `BOOKWORM_DATA_DIR` | `tests/test_platform.py` or `tests/cli/` |
| **Records** | the committed `data/` is valid | the real `data/` | PLT-002 |

**Rules are tested once, at the layer that owns them.** A lookup rule is a service test; the command test checks only the exit code and output.

## 2. Isolation

- **Each test gets its own empty `data/`** (`data_dir` fixture, under `tmp_path`) and `Settings` pointing at it (`settings` fixture). Nothing is shared between tests.
- **The adapter registry is process-global**: the autouse `reference_adapters` fixture registers the reference adapters before each test and removes them after. A test that registers another adapter removes it too.
- **No network** in the default suite. HTTP goes through `open_clients(settings, transport=httpx.MockTransport(...))`. Tests that need the network are `@pytest.mark.live`, deselected by default, run with `make test-live`.

## 3. Fixtures: factories, not singletons

```python
catalogue = make_catalogue(data_dir, access=[{"adapter": "fake.memory", "options": {"records": [fake_record(isbns=[ISBN])]}}])
library = make_library(data_dir, catalogue=catalogue.slug, catalogue_location="CENTRAL")
```

- **Factories are plain functions** in `tests/_fixtures/records.py`, taking `data_dir` and keyword overrides, writing a real file through `write_record` and loading it through the repository: they can't build a record the app would reject.
- **Unique by default** (random slug suffix), **allowed by default** (`automation: allowed`, `robots_checked_on`, no pacing), so a test only states what it's about.
- **pytest fixtures are for infrastructure** (`data_dir`, `settings`, the adapter registry), registered in `tests/conftest.py` from `tests/_fixtures/`.

## 4. Reference adapters and recordings

- `tests/_adapters/fake.py` holds real implementations of the port, as Kalens' and Xolo's `tests/_host/` holds a real host: `fake.memory` (answers from its options, or raises the `CatalogueError` named in `fail_with`; logs searches), `fake.isbn_only`, `fake.http` (a real API adapter's shape over recordings).
- **Recordings** live in `tests/_recordings/<system>/`, one file per scenario, named for what it shows, trimmed, with no personal data. Replay them with `httpx.MockTransport` (see `tests/modules/catalogues/test_port.py`).
- When a real adapter breaks, record the new response *first*, add it as a failing test, then fix the mapping.

## 5. Test IDs and markers

- **Every test carries its story's test ID**: `@pytest.mark.test_id("CAT-004")` (`tests/_plugins/test_ids.py`, from Sinapsis and Xolo). Malformed IDs stop the run. A behaviour without an ID isn't built (`docs/WORKFLOW.md`).
- `make test ID="CAT-004 CAT-005"` runs only those.
- Markers are declared in `pyproject.toml` and enforced by `--strict-markers`: `test_id`, `live`.

## 6. Style

- **Plain `async def test_*` / `def test_*` functions**; `asyncio_mode = auto`.
- **Names say the behaviour and the outcome**: `test_a_failing_catalogue_fails_only_its_libraries`.
- **`parametrize` with `ids=`** for tables of cases.
- **Arrange, act, assert**, visibly: factories at the top, one action, assertions.
- **Assert on what the test created**, by slug or record id, not on global counts.
- **Comments say why a case exists** when the name can't: `# the file name is the slug; a second source of truth would drift`.

## Checklist

- [ ] At the layer that owns the behaviour; rules not re-tested through the CLI
- [ ] Own `data_dir`; records from factories; no shared state left behind
- [ ] No network unless `@pytest.mark.live`; HTTP replayed from recordings
- [ ] Reference adapters, not mocks, for the catalogue side
- [ ] Test ID on every test; `make verify` green
