---
name: create-adapter
description: Write a catalogue adapter, the code that searches one kind of catalogue one way (a REST API, HTML pages, a headless browser) and turns its answer into bookworm's canonical BibRecord/Holding models behind the gateway. Use for "support VuFind", "add an HTML fallback for Aleph", "Vasconcelos needs Playwright", "the Nautilo adapter broke", or a new access method for software we already support.
---

# Create a catalogue adapter

Bookworm's unified internal API over catalogues is **ports and adapters**. The lookup service asks one question, *search this catalogue for this book*, through `CatalogueGateway`. The gateway reads the catalogue's record and tries its access methods in order; each one is an **adapter**: a subclass of `Adapter` (`src/bookworm/modules/catalogues/port.py`) registered under `<system>.<method>`.

```
lookup service ──► CatalogueGateway.search(catalogue, query)
                     │  automation allowed? access methods, in order:
                     ▼
                   Adapter (port) ── vufind.api ──┐
                                  ── vufind.html ─┤ raw JSON/HTML/DOM
                                  ── <site>.browser┘
                                        │ Raw* models → mapping.py (pure)
                                        ▼
                   list[BibRecord] (canonical) ──► CatalogueSearch
```

An adapter's whole job: **fetch, parse into `Raw*`, map to canonical**. Pacing, error translation, fall-through, concurrency, "may we ask" and which library a copy belongs to are already done elsewhere. Don't redo them.

## 0. Before you start

- **Does one exist for this software?** `registered_ids()` and `src/bookworm/modules/catalogues/adapters/`. A second VuFind catalogue is a record (`add-catalogue`), not an adapter. A VuFind catalogue with odd paths is an *option* on the existing adapter, not a copy of it.
- **Is the catalogue `automation: allowed`?** Don't build against a site whose robots.txt or terms say no (`add-catalogue` step 1). The live test will hit it.
- **Pick the method.** Machine interface (REST API, SRU, OAI) > HTML over `httpx` > browser (Playwright). Use the browser only when the results need JavaScript or a session the HTML route can't get; it's slow and heavy for them and us.
- **Story first.** This is a CAT story with test IDs (`create-story`). Its cases come from recordings, so record first (step 1), then write the cases.

## 1. Look and record

Run the searches yourself and save what comes back. These files are the adapter's spec and its tests.

```sh
mkdir -p tests/_recordings/<system>
curl -s -A "bookworm/0.1 (library availability checker)" '<base>/api/v1/search?lookfor=9781607322221&type=ISN' \
  > tests/_recordings/<system>/search_isbn_hit.json
```

Record, at least: a search with hits (and copies, if the source shows them), a search with no hits, a record whose copies are on loan or reference-only, and anything odd you see (ISBN-10s, several editions, missing years). Name each file for what it shows. **Trim** them to what the test needs and **never commit personal data** (patron names on holds, session cookies, tokens). For a browser adapter, save the rendered HTML (`await page.content()`) the parser reads.

## 2. Lay out the package

One sub-package per system (or per site, for `custom` catalogues), one module per access method, one shared mapping:

```
src/bookworm/modules/catalogues/adapters/vufind/
  __init__.py
  raw.py       # Raw* models: the source's shapes, only the fields we read
  mapping.py   # pure functions Raw* → BibRecord / Holding; status tables
  api.py       # VufindApiAdapter, id "vufind.api"
  html.py      # VufindHtmlAdapter, id "vufind.html" (same mapping, different raw)
```

Then import each adapter module in `adapters/__init__.py`. Nothing is discovered automatically.

## 3. Raw models and mapping

```python
# raw.py — the source's shape, never seen outside this package
class RawVufindRecord(CoreModel):
    id: str
    title: str
    isbns: list[str] = []
    publicationDates: list[str] = []


# mapping.py — pure: no I/O, no context, no settings
STATUS = {
    "available": HoldingStatus.available,
    "checked out": HoldingStatus.on_loan,
    "on reserve": HoldingStatus.on_site_only,
}

def to_holding(raw: RawVufindItem) -> Holding:
    text = raw.status.strip()
    return Holding(
        location=raw.location, location_code=raw.location,
        call_number=raw.callnumber,
        status=STATUS.get(text.lower(), HoldingStatus.unknown),
        status_text=text,          # always keep the catalogue's own words
    )
```

- **`Raw*` models use `CoreModel`** (extra fields ignored: sources add fields all the time) and declare only what the mapping reads. A required field the source dropped is a `ValidationError` → `CatalogueChangedError`.
- **Map, don't guess.** An unmapped status is `HoldingStatus.unknown` with `status_text` kept; add it to the table when you see it. A year that doesn't parse is `None`. ISBNs go through `normalize_isbn`; drop the ones that fail rather than failing the record.
- **`holdings=None` vs `()`**: `None` when this method doesn't fetch copies, `()` when it did and there are none. The lookup reports these differently.
- **`location_code`** is what libraries' `catalogue_location` is matched against: use the most stable code the source gives (a building or sub-library code, not a display name that may be translated).
- Records come back **in the catalogue's order, unfiltered**. Deciding which match the query (exact vs possible) is the lookup's job.

## 4. The adapter

```python
class VufindApiOptions(AdapterOptions):
    """What a catalogue record's `access[].options` may set for vufind.api."""
    api_path: str = "/api/v1"
    limit: int = Field(default=20, ge=1, le=100)


@register
class VufindApiAdapter(Adapter):
    id = "vufind.api"
    supports = frozenset({QueryKind.isbn, QueryKind.title_author})
    Options = VufindApiOptions

    async def search(self, query: BookQuery) -> list[BibRecord]:
        assert isinstance(self.options, VufindApiOptions)
        params = _params(query, limit=self.options.limit)
        response = await self.context.get(f"{self.context.base_url}{self.options.api_path}/search", params=params)
        try:
            raw = RawVufindSearch.model_validate_json(response.content)
        except ValidationError as exc:
            raise CatalogueChangedError(f"{self.options.api_path}/search: unexpected JSON: {exc}") from exc
        return [to_bib_record(r, base_url=self.context.base_url) for r in raw.records]
```

- **Only `self.context` and `self.options`.** `context.get()` paces requests to this catalogue and translates timeouts, connection errors, 401/403/429 and 4xx/5xx into `CatalogueUnavailableError` / `CatalogueBlockedError`. Never import `httpx` to make requests, read settings, the directory, or files.
- **Raise only `CatalogueError` subclasses** (`shared/errors.py`), each with a detail saying *where* and *what was expected*: `CatalogueChangedError` (shape changed: the adapter needs fixing), `CatalogueBlockedError` (CAPTCHA, login wall in a 200), `UnsupportedQueryError` (this form can't do that query). The gateway records it and tries the next method. Anything else is a bug and will crash the lookup, on purpose.
- **`supports`** lists only the query kinds the method really handles; the gateway skips it for the others.
- **Options** are per-catalogue knobs (paths, limits, facet names), validated when the record is checked. Defaults should fit a stock install. Never put a URL here that belongs in `base_url`.
- **Return `[]` only for "the catalogue said: nothing found".** A page that didn't load properly is an error, not an empty result.
- **More than one request per search** (results, then holdings) is fine; each goes through `context.get()`. Keep it bounded (an option like `holdings_for_first: 5`).

### Browser adapters

```python
page = await self.context.page()          # paced; Chromium launched on first use
try:
    await page.goto(f"{self.context.base_url}/buscar", wait_until="domcontentloaded")
    await page.fill("#titulo", query.title or "")
    await page.click("button[type=submit]")
    await page.wait_for_selector(".resultado, .sin-resultados", timeout=15_000)
    html = await page.content()
finally:
    await page.context.close()
return [to_bib_record(r) for r in parse_results(html)]   # parse_results: pure, tested on saved HTML
```

Translate Playwright's `TimeoutError` to `CatalogueUnavailableError` (or `CatalogueChangedError` if the page loaded but the selector never appeared). Keep the browser part as thin as possible: get the HTML, then parse it with the same pure functions an HTML adapter would use.

## 5. Test it

Tests mirror the package: `tests/modules/catalogues/adapters/<system>/`.

- **Mapping tests** (pure, no I/O): one per recording or status-table entry. ISBN normalization, `holdings` None vs (), unknown statuses kept as `unknown` with `status_text`.
- **Adapter tests** through the gateway with `httpx.MockTransport` serving the recordings (see `tests/modules/catalogues/test_port.py`): the request the adapter sends (path, params), the records it returns, and `CatalogueChangedError` on a recording whose shape is wrong.
- **One `live` test** (`@pytest.mark.live`) against the real catalogue, with a book it's known to hold: asserts the search answers and returns at least one record. It never runs in CI; run it with `make test-live ID=…` before closing the story, and whenever the adapter breaks.
- Every test carries its story's test ID.

## 6. Wire it

- Add the adapter to the catalogue records that should use it (`add-catalogue` step 3), and run `make check-records`.
- Run one real `bookworm find` and paste the result in the PR.
- If the catalogue's libraries' copies don't show up, check their `catalogue_location` against the `location_code`s the mapping produces.

## Checklist

- [ ] No existing adapter or option already covers it; the catalogue is `automation: allowed`
- [ ] Recordings in `tests/_recordings/<system>/`, trimmed, with no personal data
- [ ] `Raw*` models + pure `mapping.py`; `status_text` kept; unknowns are `unknown`/`None`, not guesses
- [ ] Adapter uses only `context.get()` / `context.page()` and `self.options`; raises only `CatalogueError`s with where/what details
- [ ] `supports` and `Options` accurate; registered in `adapters/__init__.py`
- [ ] Mapping and recorded-response tests with test IDs; one `live` test run once
- [ ] Records wired, `make check-records` and `make verify` green
