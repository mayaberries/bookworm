# 🗺️ Bookworm: roadmap

→ [Workflow](WORKFLOW.md) · [Boards](boards/README.md) · [Decisions](DECISIONS.md)

> Bookworm answers "is this book at that library?" for Mexico City, where no single catalogue covers every library. It gets there in four stages: a foundation that can hold any library and talk to any catalogue, a census of the city's libraries, adapters for the catalogues that cover most books, then the long tail and day-to-day use.

## 🧭 Stages

|#|Stage|Milestone|Label|In one line|
|---|---|---|---|---|
|1|[Foundation](stages/01-foundation.md)|Foundation|`stage:foundation`|Records, the adapter port, the gateway and the lookup, proven with reference adapters|
|2|[Census](stages/02-census.md)|Census|`stage:census`|A record for every library in the city we can find, with how (or whether) its catalogue can be asked|
|3|[First catalogues](stages/03-first-catalogues.md)|First catalogues|`stage:catalogues`|Real adapters for the catalogues that hold most of the books: VuFind first|
|4|[Coverage](stages/04-coverage.md)|Coverage|`stage:coverage`|The remaining catalogues, results kept between runs, and a nicer way to ask|

### 1 · Foundation ← current

- Python package, CLI, harness and CI.
- Library and catalogue records as Markdown files, validated by models, with a check for the whole folder.
- The adapter port, the registry and the gateway, with reference adapters in `tests/_adapters/`.
- The lookup: one search per catalogue, each library's share of the answer.

### 2 · Census

- The public network (alcaldía branches), UNAM's libraries, the large federal and university collections.
- Each catalogue's robots.txt and terms checked, so its `automation` is known.

### 3 · First catalogues

- VuFind (API, then HTML) for UNAM Descubridor, Nautilo and UAM Iztapalapa.
- Biblioteca Vasconcelos, if its terms allow.

### 4 · Coverage

- Aleph, Koha, Janium or whatever else the census finds, ordered by how many libraries each unlocks.
- Keeping results between runs, and the way people ask (CLI only, a bot, a page).

## ❓ Cross-stage open decisions

|Decision|Blocks|
|---|---|
|GitHub repo: name, owner and visibility. Until it exists, stories have no issues and the ticket skills stop at the draft|Every story's Issue column|
|How census data is collected: by hand from directories, or importer scripts per source (the CDMX network's directory, UNAM's). An importer would be a new kind of code (a source → records)|Census|
|Where results are kept between runs, if at all: none, JSON files, SQLite|Coverage|
|Whether to use WorldCat for collections no catalogue of ours reaches|Coverage|
