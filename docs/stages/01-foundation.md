# 🧱 Foundation: records, adapters and the lookup, proven offline

← [Roadmap](../ROADMAP.md) · Next: [Census](02-census.md) →

Build the parts every later stage fills in: record files for libraries and catalogues, the port every catalogue adapter implements, the gateway that tries a catalogue's access methods in order, and the lookup that turns catalogue answers into per-library availability. Everything is proven with reference adapters and recorded responses; no real catalogue is wired yet.

📍 Milestone: Foundation · label `stage:foundation`

## 🎬 What the stage demonstrates

- `bookworm records check` validates every record, the slugs they name and each catalogue's access methods.
- `bookworm find --isbn …` answers for every library on record: from a catalogue, "check by hand", or "search failed", never a crash.
- A new adapter is a subclass and one import; a new catalogue running known software is a file.

## ✅ Exit criteria

- All test IDs assigned to this stage are green
- `make verify` is green locally and in CI
- The workflow and architecture skills exist and match the code

## 🧩 Stories

In build order. Stories 1–4 were built before the GitHub repo existed, so they have no issues.

|#|Story|Issue|Test IDs|
|---|---|---|---|
|1|Package, CLI, test harness with test IDs ([PLT](../boards/PLT.md))|—|PLT-001–PLT-003|
|2|Library and catalogue records: models, files, the record check ([DIR](../boards/DIR.md))|—|DIR-001–DIR-008|
|3|Adapter port, registry and gateway, with reference adapters ([CAT](../boards/CAT.md))|—|CAT-001–CAT-009|
|4|Lookup: one search per catalogue, each library's share ([LKP](../boards/LKP.md))|—|LKP-001–LKP-006|
|5|GitHub repo, CI required on `main` ([PLT](../boards/PLT.md))|||

### 📝 Story notes

1. **Harness.** uv, pinned dependencies, Makefile (`install`, `test`, `test-live`, `lint`, `typecheck`, `check-records`, `verify`), the test-ID plugin from Xolo, import-linter contracts, the CLI's error → exit code mapping.
2. **Records.** `LibraryRecord`, `CatalogueRecord`, file-backed repositories, `DirectoryService.check_records`, templates in `data/_templates/`, seed records from the README's landscape table.
3. **Adapters.** `Adapter`, `AdapterContext` (paced `get()`/`page()`, error translation), the registry, `CatalogueGateway` with fall-through, `check_access`, the `fake.memory` and `fake.http` reference adapters and a recorded response.
4. **Lookup.** `LookupService.find`, outcomes per library, exact vs possible ISBN matches, concurrency across catalogues.
5. **GitHub.** Blocked on the repo decision (roadmap). `.github/workflows/ci.yml` already runs `make verify`; make it a required check on `main`.

## ❓ Open decisions

- None beyond the roadmap's.

## ✔️ Decisions made

- Records are Markdown files with YAML frontmatter ([decisions](../DECISIONS.md#records-are-markdown-files-with-yaml-frontmatter)).
- Catalogue adapters: ports and adapters behind one gateway ([decisions](../DECISIONS.md#catalogue-adapters-ports-and-adapters-behind-one-gateway)).
- Only `automation: allowed` catalogues are queried; `unknown` counts as no.
