---
name: create-model
description: Create or change a Pydantic model in bookworm (a record's fields, a query, a canonical book model, an adapter's Raw* or Options model, a report), with its role, base, naming and validation rules. Use for "libraries need opening hours", "add an edition to BibRecord", "the query should accept a year", "ratings must be 1 to 5".
---

# Create a model

Adapted from the `create-model` skill shared by Vetted, Sinapsis, Kalens and Xolo. Same idea: **a model is a shape and the rules only about that shape, and its name says where the value came from and where it's going.** Bookworm has no HTTP API and no tables, so the roles are different:

| Role | Is | Comes from → goes to | Base | Where |
|---|---|---|---|---|
| `XRecord` | **exactly a record file's frontmatter** | file → repository | `InputModel` | `modules/directory/schemas.py` |
| `X` (`Library`, `Catalogue`) | the record plus `slug` (file name) and `notes` (body) | repository → everything | the `XRecord` | same |
| `<Thing>Query` | what a person asks (`BookQuery`) | CLI → service | `InputModel` | the module's `schemas.py` |
| canonical (`BibRecord`, `Holding`) | **the one shape every catalogue's answer becomes** | adapter → gateway → lookup | `FrozenModel` | `modules/catalogues/schemas.py` |
| `Raw<Thing>` | a source's shape (JSON, a parsed HTML row) | source → adapter's mapping, **never further** | `CoreModel` | the adapter's `raw.py` |
| `<Adapter>Options` | what a catalogue record may set for one adapter | `access[].options` → adapter | `AdapterOptions` | the adapter's module |
| results (`CatalogueSearch`, `AvailabilityReport`) | a use case's answer | service → CLI | `FrozenModel` | the module's `schemas.py` |

The bases are in `src/bookworm/shared/schemas.py`: `CoreModel`, `InputModel` (`extra="forbid"`: a typo'd key or option is an error, not silently ignored), `FrozenModel` (values passed between layers can't be changed by the next layer).

## 0. Before you start

- **Record models are a format.** Every file in `data/` follows them. Adding an optional field is free; renaming or removing one, or making one required, is a change to every file: do it in one PR with all files updated and `make check-records` green.
- **Canonical models are the contract between adapters and the rest.** A field added there must be fillable by at least one adapter, and `None` for the rest. Never add a field only one source has as required.
- **`Raw*` models stay in their adapter's package.** If another module needs a value from one, it belongs in the canonical model.

## 1. Rules

- **Record fields mirror what a person can check.** Prefer enums (`Alcaldia`, `Lending`) to free text where the values are known; free text (`address`, notes) where they aren't. Unknown is `None` (or an `unknown` enum member), never a guessed default.
- **Defaults are honest.** `automation: unknown`, `verification.status: unverified`, `lending: unknown`. A default that claims something (`allowed`, `verified`) is a bug waiting to be shipped.
- **Reusable constraints are `Annotated` aliases** (`Slug`, `Isbn`, `AdapterId`), not repeated `Field(...)`s.
- **Normalise in validators** so stored and compared values are canonical (`normalize_isbn`; blank strings → `None` on queries).
- **Validators raise `ValueError`, never `assert`**, and say what was expected: `"'12345' isn't an ISBN: expected 10 or 13 digits"`.
- **Cross-field rules are `model_validator(mode="after")`** (`BookQuery`: an ISBN, or title/author, not both).
- **No I/O, settings or "now" in models.** Pure functions about one model's fields may live next to it (`normalize_isbn`), and say why there.
- **Enums are `StrEnum`** with values that read well in YAML (`members_only`, `on_site_only`).
- **Tuples, not lists, in frozen models** (`authors: tuple[str, ...]`), so they're really immutable.
- **`None` vs empty means something**: `holdings=None` (not fetched) vs `()` (none). Document it on the field when it does.

## 2. Test it

Model tests are plain, no files, no network (`tests/modules/<module>/test_schemas.py`):

- each constraint at its edges, each validator both ways, each cross-field rule both ways (`parametrize` with `ids=`);
- unknown fields rejected on `InputModel`s;
- for a new record field: a record file with it loads; one with a bad value fails `check-records` naming the field.

Every test carries its story's test ID.

## Checklist

- [ ] The model has one of the roles above, its base and its name
- [ ] Inputs and records are `InputModel`; values between layers are `FrozenModel`; `Raw*` stays in its adapter
- [ ] Defaults are honest; unknowns are `None` / `unknown`
- [ ] Constraints are `Annotated` aliases; validators raise `ValueError` saying what's expected
- [ ] No I/O, settings or "now" in the model
- [ ] Record field changes update every file in `data/`, and the templates; `make check-records` green
