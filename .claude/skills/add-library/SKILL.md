---
name: add-library
description: Add or correct a library's record in data/libraries/ (name, alcaldía, contact, which catalogue lists its books and how that catalogue names it, lending, verification). Use for "add the Benjamin Franklin library", "map Coyoacán's branches", "this library moved", or any census work on libraries. For the catalogue software a library uses, see add-catalogue.
---

# Add a library record

A library record is **a building with shelves**: where it is, how to reach it, and which catalogue (if any) lists its books. It's data, not code: the "migration" for it is a pull request with the file, and its "test" is `make check-records` plus a person checking the source. Board: MAP (DIR only if the record's *fields* must change).

## 0. Before you start

- **Is it already there?** `uv run bookworm libraries list` or `ls data/libraries/`. Correcting a record beats adding a duplicate under a new slug.
- **Is it a library or a catalogue?** UNAM Descubridor is a catalogue; the Biblioteca Central is a library listed in it. One building, one library record, however many catalogues mention it.
- **Where does the data come from?** Every record names its source (`verification.source`). Don't fill fields from memory or guesses: leave them `null` and say so in the notes. An honest `null` is better than a plausible address.

## 1. Pick the slug

The file name is the slug: lowercase, ASCII, hyphens, `^[a-z0-9]+(-[a-z0-9]+)*$`. Use the library's common name without accents or articles that add nothing: `biblioteca-vasconcelos`, `biblioteca-central-unam`, `biblioteca-publica-coyoacan-jose-marti`. Slugs are referenced by other records (`interlibrary_loan`), so don't rename one in passing; renaming means updating every reference in the same change.

## 2. Write the file

Create `data/libraries/<slug>.md` from `data/_templates/library.md` (in Obsidian: new note in `data/libraries/`, then *Templates: Insert template* → `library`; or copy the file). The fields are `LibraryRecord` in `src/bookworm/modules/directory/schemas.py`, which is the source of truth; unknown keys are an error.

```markdown
---
name: Biblioteca Central
kind: academic
alcaldia: Coyoacán
address: Circuito Interior s/n, Ciudad Universitaria
contact:
  website: https://example.unam.mx
catalogue: unam-descubridor
catalogue_location: BC          # how Descubridor names this library
lending: members_only
verification:
  status: verified
  checked_on: 2026-11-09
  source: Descubridor's "building" facet and the library's own site
---

Opening hours, how the public gets in, what was checked and how.
```

- **`catalogue`** is a slug in `data/catalogues/`, or `null` when the library has no online catalogue (most alcaldía branches). With `null`, lookups tell people to call or visit, so `contact` and `address` matter most there.
- **`catalogue_location`** is needed only when the catalogue is shared. It's the code the catalogue puts on this library's copies (a VuFind building facet, an Aleph sub-library), matched against each `Holding`'s `location_code` or `location`. Find it in the catalogue itself (a facet list, a holdings table), not by guessing.
- **`alcaldia`** must be one of the 16 names in `Alcaldia`, with accents (`Cuauhtémoc`, `Álvaro Obregón`).
- **`lending`**: `public`, `members_only` (e.g. UNAM community; the public may read on site), `on_site_only`, `unknown`.
- **`verification.status`**: `verified` (someone loaded the page or called), `inferred` (deduced from docs or similar sites), `unverified`. Date it.
- **Notes** (the body) are for people: hours, how to get a card, what didn't work. No personal data about staff or patrons.

## 3. Check it

```sh
make check-records            # every record, the slugs they name, catalogue access methods
uv run bookworm libraries show <slug>
```

`check-records` must be green: it's in `make verify` and CI, and PLT-002 fails the suite on an invalid committed record.

## 4. Many at once (census)

For a batch (an alcaldía, a university), one task per batch, each record sourced. If you're writing a script to produce records from a directory, stop: importers are an open decision (`docs/stages/02-census.md`). Until it's made, a throwaway script in the scratchpad that writes files through `LibrariesRepository.save` is fine, and the records it produces are reviewed like hand-written ones.

## Checklist

- [ ] Not a duplicate; slug follows the pattern; file name is the slug (no `slug:` field)
- [ ] `catalogue` exists in `data/catalogues/` or is `null`; `catalogue_location` set if the catalogue is shared, found in the catalogue itself
- [ ] No guessed values: unknowns are `null`, explained in the notes
- [ ] `verification` has a status, a date and a source
- [ ] `make check-records` green
