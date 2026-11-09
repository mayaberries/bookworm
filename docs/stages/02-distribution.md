# 📦 Distribution: install it anywhere, use it from an agent

← [Foundation](01-foundation.md) · Next: [Census](03-census.md) →

Make bookworm something a person installs, not a repo they clone: a tagged package that carries its records, finds its data without a repo around it, reads per-user settings, and speaks JSON to whatever drives it. Ship the Claude Code skills an installed user needs as a plugin, so the same answers work in a terminal, inside an Obsidian vault, from an agent, and later from a UI. Adapted from a sibling project's packaging issue (a QA suite turned into `uv tool install` + `init` + `doctor` + a Claude Code plugin); what didn't carry over is in the story notes.

📍 Milestone: Distribution · label `stage:distribution`

## 🎬 What the stage demonstrates

- On a machine with no clone, `uv tool install` of a tag, then `bookworm init` and `bookworm doctor`, gives a working setup; `bookworm find --isbn …` answers from the records the package carries.
- `bookworm vault init ~/libros` makes an Obsidian vault with every record and the Directory Board; after an upgrade, `bookworm vault update` brings in new records and never overwrites one the user edited.
- In Claude Code, outside this repo, the bookworm plugin's skills find a book, add a library to the user's vault, and say when the installed `bookworm` and the plugin disagree on version.
- An agent gets one JSON document per command, a failure kind that tells it whether to retry, and no way to make bookworm query a catalogue that hasn't said yes.

## ✅ Exit criteria

- All test IDs assigned to this stage are green, including the install test in CI
- A tagged release exists, with `CHANGELOG.md`, and the plugin and package versions match
- Someone other than the author completes the README's install steps on their own machine
- `make verify` is green locally and in CI

## 🧩 Stories

In build order. Stories 1–5 don't need the GitHub repo; story 6 needs Foundation's story 5 (the repo) for the install URL and the plugin marketplace.

|#|Story|Issue|Test IDs|
|---|---|---|---|
|1|Records travel with the package: bundled snapshot, data directory lookup, vaults ([PLT](../boards/PLT.md))|—|PLT-004–PLT-010|
|2|Per-user settings, `init`, `doctor` and `--version` ([PLT](../boards/PLT.md))|—|PLT-011–PLT-015|
|3|The agent contract: JSON from every command ([PLT](../boards/PLT.md))|—|PLT-016–PLT-018|
|4|Safe for agents: the automation gate holds, failures say whether to retry, one run for many ISBNs ([LKP](../boards/LKP.md))|—|LKP-007–LKP-010|
|5|The Claude Code plugin: user skills, version check, one copy in the repo ([PLT](../boards/PLT.md))|—|PLT-019–PLT-022|
|6|Installable from a tag: dependency ranges, wheel contents, install test, release ([PLT](../boards/PLT.md))|—|PLT-023–PLT-026|
|7|MCP server, a second entry point (`bookworm[mcp]`) ([PLT](../boards/PLT.md))|—|PLT-027–PLT-029|

### 📝 Story notes

**What carried over from the source issue, and what didn't.** It packaged a test suite whose clone-only setup, `.env` and skills tied it to one machine. Here the package already has a `src/bookworm` layout and a `bookworm` script, so there's no import-name collision to fix. Its tests don't ship (they were the product there; here they're dev tooling), so there's no pytest plugin. Its shared-board safeguards become catalogue safeguards (story 4): what many installs share here is the real catalogues' patience. Its "`doctor` never signs in" becomes "`doctor` never contacts a catalogue".

#### 1. Records travel with the package

Today an install has code and no records: `Settings.data_dir` defaults to `REPO_ROOT / "data"`, which points into `site-packages`. This story bundles the records, replaces `REPO_ROOT` with a lookup, and gives users a vault of their own.

- **Bundled snapshot.** `data/libraries/` and `data/catalogues/` go into the wheel as `bookworm/_data/` (hatch `force-include`), with the vault scaffold: `data/_templates/`, `Directory Board.md` and the portable `.obsidian/` files (settings, the Dataview manifest, the snippet). `data/` stays the only copy in the repo. The snapshot is read-only.
- **Data directory lookup**, first match wins: `--data-dir` (a global option) → `BOOKWORM_DATA_DIR` → `data_dir` in the config file (story 2) → the nearest vault at or above the current directory → the bundled snapshot. The resolver reports which source won; `doctor` shows it.
- **A vault** is a folder with a `bookworm.toml` marker at its root and the repo's layout (`data/libraries`, `data/catalogues`, `data/_templates`, `Directory Board.md`, `.obsidian/`), so the board's Dataview paths work unchanged. The repo gets a marker too and is a vault like any other; that's what keeps `uv run bookworm` working from a clone.
- **`bookworm vault init [path]`** copies the snapshot's records and the scaffold, and writes `.bookworm/snapshot.json`: the package version and a hash of each copied record. That's the base `status` and `update` compare against.
- **`bookworm vault status` / `update`.** Per record: new upstream, changed upstream, edited here, only here. `update` adds new records, refreshes ones not edited here, and lists the rest as conflicts to merge by hand. It never overwrites an edited record and never deletes one.
- Writes into the snapshot aren't possible; the record skills (story 5) say to make a vault first when `doctor` reports the bundled snapshot.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-004|Given each combination of `--data-dir`, `BOOKWORM_DATA_DIR`, a config file `data_dir`, a vault above the current directory and the bundled snapshot, when the data directory is resolved, then the first in that order wins and the result names its source|—|⬜|
|PLT-005|Given a vault, when a command runs from a subfolder of it (`data/libraries/`), then it uses that vault's records|—|⬜|
|PLT-006|Given the repo (which has a `bookworm.toml`), when a command runs from its root with nothing else configured, then the records are the repo's `data/` (no `REPO_ROOT` left in the code)|—|⬜|
|PLT-007|Given an empty folder, when `bookworm vault init <folder>` runs, then it holds the marker, `.bookworm/snapshot.json`, every bundled record, the templates, `Directory Board.md` and the portable `.obsidian/` files, and `bookworm records check` passes in it|—|⬜|
|PLT-008|Given a non-empty folder that isn't a vault, when `vault init` runs on it, then it exits 2 and the folder is unchanged|—|⬜|
|PLT-009|Given a vault where one record was edited, one added by hand, and a newer snapshot with one new and one changed record, when `vault status --json` runs, then each record is reported as edited here, only here, new upstream or changed upstream|—|⬜|
|PLT-010|Given the vault of PLT-009, plus a record changed both upstream and here, when `vault update` runs, then the new record is added, the record changed only upstream is refreshed, the edited and conflicting records are byte-for-byte unchanged and listed as conflicts, nothing is deleted, and the snapshot file records the new version|—|⬜|

#### 2. Per-user settings, `init`, `doctor` and `--version`

- **Config file:** `$XDG_CONFIG_HOME/bookworm/config.toml`, default `~/.config/bookworm/config.toml` on every OS (not macOS' Application Support: one path to document), read through pydantic-settings' TOML source. Order: init arguments → `BOOKWORM_*` environment → `.env` in the current directory (dev) → the config file → defaults. Unknown keys are an error naming the file, as in records. There are no credentials yet; future keys (WorldCat) go here or in the environment, never in the package. The `add-setting` skill learns the file.
- **`bookworm init`** asks for the vault (an existing one, a new one via `vault init`, or none: the bundled snapshot) and `browser_headless`, then writes the config file. `--vault PATH --yes` for no prompts. Re-running shows the current values as defaults.
- **`bookworm doctor [--json]`** checks the Python version, the bookworm version, the config file, the data directory and its source, `records check` on it, and Chromium. Chromium is a *warning*, not a failure, unless an allowed catalogue lists a browser adapter. Each failed check names its fix (`uvx playwright install chromium`, `bookworm vault init`). Exit 0 only when every required check passes. **`doctor` never contacts a catalogue**: checking whether a catalogue is up is a search, and searches are paced and gated.
- **`bookworm --version`** reads the package metadata; the HTTP User-Agent carries the same version (it says `0.1` by hand today) and still names no person.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-011|Given a config file under a temporary `XDG_CONFIG_HOME` and a `BOOKWORM_*` variable for one of its keys, when settings load, then the variable wins, the other keys come from the file, and an unknown key fails with the file's path in the message|—|⬜|
|PLT-012|Given no config file, when `bookworm init --vault <path> --yes` runs, then the config file is written with that vault; when `init` runs again with no options, it offers the saved values and keeps them|—|⬜|
|PLT-013|Given a setup with each required check broken in turn (bad config file, missing data directory, an invalid record, Chromium missing while an allowed catalogue uses a browser adapter), when `doctor --json` runs, then that check fails with a fix, the others pass, and the exit code is non-zero; with everything fine, it exits 0|—|⬜|
|PLT-014|Given an allowed catalogue with access methods, when `doctor` runs, then no HTTP request is sent and no browser starts (an httpx transport and a page factory that fail the test if called)|—|⬜|
|PLT-015|When `bookworm --version` runs, then it prints the installed package's version, and the HTTP client's User-Agent carries that same version|—|⬜|

#### 3. The agent contract: JSON from every command

The CLI's `--json` is the interface the skills, the MCP server (story 7) and a future UI all build on, so its shapes are a contract: changing one is a CHANGELOG entry, not a side effect.

- Every command takes `--json`, including `records check`, `doctor`, `vault *` and `init --yes`. With it, stdout is exactly one JSON document; anything for people goes to stderr.
- Errors under `--json` are `{"error": {"kind": "...", "detail": "..."}}` on stdout, with the existing exit codes (2 bad input, 3 not found, 4 invalid records).
- Each command's output is a Pydantic model; snapshot tests of their JSON schemas catch accidental changes.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-016|Given every command, when it runs with `--json`, then stdout parses as one JSON document and nothing else is printed on stdout|—|⬜|
|PLT-017|Given the three error cases of PLT-003, when they run with `--json`, then stdout is `{"error": {"kind", "detail"}}` with the same exit codes|—|⬜|
|PLT-018|Given the committed JSON schema of each command's output, when the output models change, then the test fails until the schema snapshot is updated on purpose|`tests/_snapshots/cli_schemas/`|⬜|

#### 4. Safe for agents

Each install is a separate client, and an agent may call `find` in a loop. Pacing is per process, so the safeguards have to live in code and in what an agent is told, not in a shared limiter.

- **The gate can't be bypassed.** `records check` already refuses access methods without `automation: allowed` and `robots_checked_on`, but a vault edited by hand can skip the check, and the gateway checks only `automation`. Make the gateway refuse a catalogue without `robots_checked_on` too. No setting, environment variable or option turns the gate off. (This task changes the gateway, so it takes the CAT label.)
- **Failures tell an agent what to do.** A `failed` library result carries the failure's kind (`unavailable`, `blocked`, `changed`, `unsupported`) and `retry`: `later` (unavailable), `not_soon` (blocked: back off), `after_fix` (changed, unsupported). The `find-book` skill says what each means.
- **Many ISBNs, one run.** `find` takes `--isbn` repeatedly, so a reading list is one process whose per-catalogue pacing covers every search, instead of N processes that each start fresh.
- A per-run cap on catalogue requests and a local result cache belong with "results kept between runs" ([Coverage](05-coverage.md)).

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|LKP-007|Given a catalogue record with `automation: allowed` and access methods but no `robots_checked_on` (as a hand-edited vault can have), when a lookup runs, then its libraries get `check_manually` with the reason and no adapter is called|`fake.memory`|⬜|
|LKP-008|Given catalogues that fail as unavailable, blocked, changed and unsupported, when a lookup runs, then each failed library's result carries that kind and the matching `retry` value, in the model and in `find --json`|`fake.memory`|⬜|
|LKP-009|Given three ISBNs and one allowed catalogue with `min_seconds_between_requests`, when `find` runs with three `--isbn`, then the catalogue is searched once per ISBN, the searches respect its pacing, and the report has one section per ISBN|`fake.memory`|⬜|
|LKP-010|Given an invalid ISBN among valid ones, when `find` runs with several `--isbn`, then it exits 2 before any catalogue is searched|—|⬜|

#### 5. The Claude Code plugin

pip doesn't put skills where Claude Code looks, so the user-facing skills ship as a plugin from this repo, with its marketplace file. That also gives users skill updates.

- **Layout:** `.claude-plugin/marketplace.json` at the root; `plugin/.claude-plugin/plugin.json`, `plugin/skills/`, `plugin/hooks/`. Add `plugin/` to `.obsidian/app.json`'s ignore filters and the `hide-code-folders` snippet.
- **Which skills go where.** Users get, in the plugin:
  - `find-book` (new): how to ask (ISBN first, several at once), how to read outcomes (`exact` vs `possible`, "check by hand" is an answer, `holdings=None` vs `()`), what each failure's `retry` means, and not to re-run a lookup without a reason.
  - `add-library`, `add-catalogue`: moved from `.claude/skills/` and rewritten to work in any vault. They call `bookworm records check`, never `make` or `uv run`. A closing section covers sending records upstream as a pull request.
  - `setup`: `bookworm init`, then `doctor`, and what each failed check means.

  The developer skills stay in `.claude/skills/`: `create-*`, `add-setting`, `write-tests`, `create-story`, `create-task`, `close-ticket`.
- **Knowledge leaves CLAUDE.md.** An installed user never loads this repo's `CLAUDE.md`, so what they need moves into the plugin skills: "never fill a field from a guess", `verification`, the `automation` gate and why, and "behaviour that looks like a bug but isn't". `CLAUDE.md` links to the skills instead of repeating them.
- **One copy in the repo.** `.claude/settings.json` adds this repo as a local marketplace (`extraKnownMarketplaces`, directory source) and enables the plugin, so contributors load the same record skills users do.
- **Version check.** A `SessionStart` hook runs `bookworm --version`. If the version matches the plugin's, it stays silent. If it differs, it prints one line with both versions and the upgrade command. If `bookworm` isn't installed, it says how to install it.
- The plugin's MCP entry (`bookworm mcp`) comes with story 7.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-019|Given the repo, when the plugin check runs, then `marketplace.json` and `plugin.json` validate (`claude plugin validate` where available, else their schemas) and `plugin.json`'s version equals `pyproject.toml`'s|—|⬜|
|PLT-020|Given every plugin skill, when its text is scanned, then it never mentions `uv run`, `make` or a repo path, and every `bookworm …` command it names exists in the CLI (resolved through Typer)|—|⬜|
|PLT-021|Given a stub `bookworm` on `PATH` reporting the plugin's version, a different version, or none at all, when the `SessionStart` hook runs, then it prints nothing, one mismatch line with both versions, or install instructions|—|⬜|
|PLT-022|Given `.claude/skills/` and `plugin/skills/`, then no skill name appears in both, and `.claude/settings.json` enables the plugin from the local marketplace|—|⬜|

#### 6. Installable from a tag

- **Dependency ranges.** Exact pins in `[project].dependencies` would make bookworm impossible to install next to anything else, as a future UI would need to. `dependencies` move to ranges, from the locked version up to the next major (`pydantic>=2.14.3,<3`). `uv.lock` stays exact, and CI and `make` run against it, so the lock keeps the "versions move deliberately" rule (see [decisions](../DECISIONS.md#dependency-ranges-in-the-package-exact-versions-in-the-lock)). Dev tools stay exact.
- **Playwright** stays a dependency (adapters import it lazily). Chromium is a separate download that `doctor` checks.
- **The install test.** `tests/test_install.py`, marked `install` (a new marker, excluded by default like `live`), runs in its own CI job (`make test-install`). It builds the wheel, installs it with `uv tool install` into a temporary tool directory, and runs commands from a temporary folder outside the repo.
- **Releases.** Tags `vX.Y.Z`, a short `CHANGELOG.md` (commands, JSON shapes, skills), with the package and plugin versions bumped together. The README's setup becomes:

  ```bash
  uv tool install git+https://github.com/<owner>/<repo>.git@v0.1.0
  bookworm init
  bookworm doctor
  # only for catalogues behind a browser adapter:
  uvx playwright install chromium
  # in Claude Code:
  /plugin marketplace add <owner>/<repo>
  /plugin install bookworm@bookworm
  ```

  Contributors keep "Working on it" (`make install`, `make verify`).
- Needs Foundation's story 5 (the GitHub repo) and the open decision below on the distribution name.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-023|Given `pyproject.toml`, then every `[project].dependencies` entry is a range with a lower bound equal to its version in `uv.lock`, and no entry is pinned with `==`|—|⬜|
|PLT-024|Given a wheel built from the repo, then it contains every record in `data/libraries/` and `data/catalogues/` and the vault scaffold, and nothing from `docs/`, `tests/`, `.claude/`, `plugin/` or `.obsidian/` beyond the scaffold's portable files|`install`|⬜|
|PLT-025|Given that wheel installed with `uv tool install` and a temporary folder outside the repo with no config, when `bookworm --version`, `doctor --json`, `libraries list --json` and `find --isbn … --json` run there, then they succeed against the bundled snapshot and `find` answers every library (no crash, "check by hand" counts)|`install`|⬜|
|PLT-026|Given the same install, when `bookworm vault init` runs in a temporary folder and then `records check` and `vault status` run inside it, then the vault is valid and up to date|`install`|⬜|

#### 7. MCP server

`--json` serves Claude Code through the skills, but an MCP server lets any agent use bookworm without a shell, and is the shape a UI's backend would take. It's a second entry point, which changes the "CLI is the only entry point" decision to "entry points (`cli`, `mcp`, later a UI) are imported by nothing, and each calls one service method per request" (see [decisions](../DECISIONS.md#entry-points-the-cli-first-mcp-and-a-ui-beside-it)).

- `bookworm mcp` starts a stdio server, from the optional extra `bookworm[mcp]` so the base install stays small. Its tools are `find_book`, `list_libraries`, `show_library`, `check_records` and `doctor`, and they return the same models as the CLI's `--json` (story 3).
- The plugin gains an `.mcp.json` entry for `bookworm mcp`.
- import-linter: add `bookworm.mcp` to the "nothing imports it" contract next to `bookworm.cli`; `shared/` imports neither.
- The SDK is pinned like any other dependency when the story starts; check its current version then, not now.

|ID|Given / when / then|Recording / source|Status|
|---|---|---|---|
|PLT-027|Given the server started in-process, when the client lists tools, then it gets the five tools with input schemas from their input models|—|⬜|
|PLT-028|Given records and a `fake.memory` catalogue, when `find_book`, `list_libraries`, `show_library`, `check_records` and `doctor` are called, then each result equals the CLI's `--json` for the same input|`fake.memory`|⬜|
|PLT-029|Given an install without the `mcp` extra, when `bookworm mcp` runs, then it exits 2 with the command that installs the extra|—|⬜|

## ❓ Open decisions

- **Distribution name and hosting.** `bookworm` is probably taken on PyPI. The import name and the command can stay `bookworm`, but the distribution name (in `pyproject.toml`, the install URL and the plugin marketplace) needs choosing with the GitHub repo (roadmap). Blocks story 6 and the marketplace half of story 5. PyPI itself can wait; installing from git tags is enough for now.
- **Whether `find --json` for several ISBNs (LKP-009) is one report per ISBN or one report with an ISBN per result.** Decide in story 4 with the JSON contract from story 3.

## ✔️ Decisions made

- Install shape: `uv tool install` from a git tag, then `bookworm init` and `doctor`. The skills ship as a Claude Code plugin from this repo, versioned with the package.
- Vaults hold copies of the records, and `vault update` merges new ones in. There's no overlay over the bundled snapshot, because Dataview can only see files in the vault ([decisions](../DECISIONS.md#records-outside-the-repo-a-bundled-snapshot-and-user-vaults)).
- `--json` is the agent contract now, and the MCP server is story 7, behind an optional extra ([decisions](../DECISIONS.md#entry-points-the-cli-first-mcp-and-a-ui-beside-it)).
- The package declares dependency ranges, and the lock stays exact ([decisions](../DECISIONS.md#dependency-ranges-in-the-package-exact-versions-in-the-lock)).
- Distribution comes before the census. The data directory lookup, the record skills and the CLI's output are cheapest to change now, before census work and its contributors build habits on `REPO_ROOT`, `make check-records` and table output.
