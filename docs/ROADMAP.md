# 🗺️ Bookworm: roadmap

→ [Workflow](WORKFLOW.md) · [Boards](boards/README.md) · [Decisions](DECISIONS.md)

> Bookworm answers "is this book at that library?" for Mexico City, where no single catalogue covers every library. It gets there in five stages: a foundation that can hold any library and talk to any catalogue, a package anyone can install and drive from a terminal, an Obsidian vault or an agent, a census of the city's libraries, adapters for the catalogues that cover most books, then the long tail and day-to-day use.

## 🧭 Stages

|#|Stage|Milestone|Label|In one line|
|---|---|---|---|---|
|1|[Foundation](stages/01-foundation.md)|Foundation|`stage:foundation`|Records, the adapter port, the gateway and the lookup, proven with reference adapters|
|2|[Distribution](stages/02-distribution.md)|Distribution|`stage:distribution`|An installable, tagged package with its records, per-user settings, `init`/`doctor`, JSON for agents and a Claude Code plugin|
|3|[Census](stages/03-census.md)|Census|`stage:census`|A record for every library in the city we can find, with how (or whether) its catalogue can be asked|
|4|[First catalogues](stages/04-first-catalogues.md)|First catalogues|`stage:catalogues`|Real adapters for the catalogues that hold most of the books: VuFind first|
|5|[Coverage](stages/05-coverage.md)|Coverage|`stage:coverage`|The remaining catalogues, results kept between runs, and a nicer way to ask|

### 1 · Foundation ← current

- Python package, CLI, harness and CI.
- Library and catalogue records as Markdown files, validated by models, with a check for the whole folder.
- The adapter port, the registry and the gateway, with reference adapters in `tests/_adapters/`.
- The lookup: one search per catalogue, each library's share of the answer.

### 2 · Distribution

- The records travel with the package; a vault of your own with `bookworm vault init`, kept current with `vault update`.
- Per-user settings in `~/.config/bookworm/config.toml`, `bookworm init` and `bookworm doctor`.
- JSON from every command, failures that say whether to retry, and an automation gate nothing bypasses.
- A Claude Code plugin with the user skills; tagged releases; later, an MCP server.

### 3 · Census

- The public network (alcaldía branches), UNAM's libraries, the large federal and university collections.
- Each catalogue's robots.txt and terms checked, so its `automation` is known.

### 4 · First catalogues

- VuFind (API, then HTML) for UNAM Descubridor, Nautilo and UAM Iztapalapa.
- Biblioteca Vasconcelos, if its terms allow.

### 5 · Coverage

- Aleph, Koha, Janium or whatever else the census finds, ordered by how many libraries each unlocks.
- Keeping results between runs, and the way people ask (CLI only, a bot, a page).

## ❓ Cross-stage open decisions

|Decision|Blocks|
|---|---|
|GitHub repo: name, owner and visibility. Until it exists, stories have no issues and the ticket skills stop at the draft|Every story's Issue column|
|How census data is collected: by hand from directories, or importer scripts per source (the CDMX network's directory, UNAM's). An importer would be a new kind of code (a source → records)|Census|
|Distribution name (PyPI, install URL, plugin marketplace); `bookworm` is probably taken on PyPI|Distribution's release story|
|Where results are kept between runs, if at all: none, JSON files, SQLite|Coverage|
|Whether to use WorldCat for collections no catalogue of ours reaches|Coverage|
