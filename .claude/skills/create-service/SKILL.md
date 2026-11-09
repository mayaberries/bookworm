---
name: create-service
description: Create or change a service in bookworm, the layer that holds a module's use cases and the rules between them (which libraries, which catalogues, what counts as available), over its repositories and the catalogue gateway. Use for "lookups should skip closed libraries", "list libraries near an alcaldía", "where does this rule go?", or a new module's use case.
---

# Create a service

Adapted from the `create-service` skill shared by Vetted, Sinapsis, Kalens and Xolo. A service holds **a module's use cases**: what a caller wants done, the rules that decide it, and the shape of the answer. Today: `DirectoryService` (records), `LookupService` (availability).

| A service does | Examples |
|---|---|
| **Use cases**, one method per thing a caller wants, named for the action | `find`, `list_libraries`, `check_records` |
| **Rules**, raised as domain errors or returned as outcomes | "a missing slug is NotFound", "a library with no catalogue is check_manually" |
| **Composition** across repositories and modules | catalogues for a set of libraries; each library's share of a search |
| **Concurrency and batching** | one search per catalogue, bounded by `max_concurrent_catalogues` |

It does **not** parse arguments or print (the CLI), read files (repositories), or talk to a catalogue (the gateway and adapters).

## 1. Shape

```python
class LookupService:
    def __init__(self, *, directory: DirectoryService, gateway: CatalogueGateway, max_concurrent_catalogues: int) -> None:
        ...
```

- **Everything injected, keyword-only**: its own repositories, other modules' services or gateways, plain config values. Nothing built inside, no `get_settings()` inside.
- **Its own repositories, other modules through their package.** `LookupService` uses `bookworm.modules.directory.DirectoryService`, never `directory.repository`. import-linter enforces this (`make lint`).
- **Wired in the module's `__init__.py`** by a builder (`build_directory_service(data_dir)`) or, when it needs open clients, an async context manager (`open_lookup_service(settings)`). The CLI uses those and nothing else.
- **No cycles.** If two modules need each other, the shared part is a third.

## 2. Use cases

- **Arguments are plain values and input models** (`query: BookQuery`, `library_slugs: list[str] | None`). A service never reads `sys.argv`, the environment or the terminal, so the same method runs from the CLI, a script, a test or (later) a bot.
- **Return models**, frozen where they cross a layer (`AvailabilityReport`). Not tuples, not dicts.
- **Errors vs outcomes.** A caller's mistake (an unknown slug, an invalid record) is a domain error (`NotFoundError`, `InvalidRecordError`). A catalogue failing during a lookup is an **outcome** (`LibraryOutcome.failed` with the attempts), because one catalogue must never fail the whole answer. Decide which per rule, and say why in a comment when it isn't obvious.
- **Each rule lives in one place.** "Only allowed catalogues are queried" is the gateway's; "which copies are this library's" is the lookup's. Don't copy a rule into a second layer "to be safe".
- **"Now" is taken once per use case** (`now = datetime.now(UTC)`) and passed down.
- **Concurrency is bounded** (`asyncio.Semaphore`) and per catalogue, not per library. Pacing within a catalogue is the gateway's `Throttle`, not the service's.

## 3. Test it

This is where most behaviour is, so most tests go here, against real record files (factories) and the reference adapters (`tests/_adapters/fake.py`); no mocks of our own code.

- each use case's happy path and the model it returns;
- one test per rule and per outcome (`parametrize` with `ids=` for tables of cases);
- for lookup rules: how many searches were made (`FakeMemoryAdapter.searches`), so batching doesn't silently regress;
- failure isolation: one failing catalogue, the others still answer.

## Checklist

- [ ] Collaborators injected keyword-only; nothing built or read from settings inside
- [ ] Other modules only through their package; wired by the module's builder
- [ ] Plain values in, models out; no argv, env or printing
- [ ] Caller mistakes are domain errors; catalogue failures are outcomes
- [ ] Each rule in one place; concurrency bounded
- [ ] Tests per rule and outcome, against real records and reference adapters
