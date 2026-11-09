---
name: add-catalogue
description: Add or correct a catalogue's record in data/catalogues/ (software, base URL, whether automated access is allowed, pacing, and which adapters to try with what options). Use for "add Nautilo", "UAM's VuFind has its API on", "check Vasconcelos' robots.txt", "wire this catalogue to vufind.html". For a library building, see add-library; for code that talks to a new kind of catalogue, see create-adapter.
---

# Add a catalogue record

A catalogue record is **software at a URL that lists books**, and everything bookworm needs to ask it: what it runs, whether we may ask, how fast, and through which adapters. Supporting a catalogue that runs software we already have an adapter for is *only* this record. Board: MAP.

## 0. Before you start

- **One record per installation**, not per library: UNAM Descubridor is one record however many libraries it covers. Libraries point at it (`catalogue:`), and say how it names them (`catalogue_location:`).
- **Look before you write.** Load the catalogue in a browser. Note the software (footer, page source, URL patterns: VuFind's `/Record/<id>`, Aleph's `/F/?func=`), a search URL, a record URL and a holdings view. Put them in the notes.

## 1. May we ask it? (`automation`)

Bookworm only sends requests to catalogues marked `automation: allowed` (`docs/DECISIONS.md`). Decide it from:

1. `<origin>/robots.txt`: is the search path disallowed for `*` or for generic bots?
2. The site's terms of use, if it has any.
3. An API's own docs (an enabled VuFind API is an invitation for its paths).

Then set `automation` (`allowed` / `disallowed`) and `robots_checked_on`, and quote the relevant robots.txt lines in the notes. **If it says no, it's `disallowed`, whatever we'd like**; lookups will tell people to search it by hand. `unknown` is treated as no.

## 2. Pace it

`min_seconds_between_requests` (default 2.0) applies across all of a catalogue's adapters during a lookup. Raise it for small institutional servers, or when robots.txt has a `Crawl-delay`. Never lower it below what the site asks for.

## 3. Wire its access methods

`access` lists adapters to try **in order**; the gateway falls through to the next when one fails (API off → HTML → browser). Each entry is a registered adapter id and that adapter's options:

```yaml
access:
  - adapter: vufind.api
  - adapter: vufind.html
    options:
      holdings: true
```

- See what's registered: `uv run python -c "from bookworm.modules.catalogues import registered_ids; print(registered_ids())"`. Each adapter's `Options` model (in its module) lists what `options` may say; unknown options are an error.
- Prefer machine interfaces first (API, SRU), HTML next, browser last: cheaper for them and for us.
- **No adapter for its software yet?** Leave `access: []`. The catalogue is still useful on record: lookups say "Bookworm can't search its catalogue yet". Writing the adapter is `create-adapter`, a CAT story.
- Listing any access method requires `automation: allowed` and `robots_checked_on`; `make check-records` fails otherwise.

## 4. Write the file

Create `data/catalogues/<slug>.md` from `data/_templates/catalogue.md` (in Obsidian: new note in `data/catalogues/`, then *Templates: Insert template* → `catalogue`; or copy the file). Keep the template's "Libraries in this catalogue" block at the end of the notes. Fields: `CatalogueRecord` in `src/bookworm/modules/directory/schemas.py`.

- `system`: `vufind`, `aleph`, `koha`, `janium`, `custom` (a one-off site), `unknown`. It's descriptive; the adapter ids decide behaviour.
- `base_url`: the catalogue's root (for VuFind, the path VuFind lives under, e.g. `https://biblioteca.izt.uam.mx/vufind`).
- `verification`: status, date, source, as in `add-library`.

## 5. Check it

```sh
make check-records
uv run bookworm find --isbn <a book you know it holds> --library <a library that points at it>
```

Run a real `find` once after wiring access methods, and say what it returned in the PR. If a library's copies don't show up, its `catalogue_location` probably doesn't match the catalogue's location codes.

## Checklist

- [ ] One record per installation; software, search URL and record URL noted
- [ ] robots.txt and terms read; `automation` and `robots_checked_on` set; relevant lines quoted in notes
- [ ] `min_seconds_between_requests` respects any `Crawl-delay`
- [ ] `access` only lists registered adapters, cheapest first, with valid options
- [ ] `make check-records` green; one real `find` run if access methods were added
