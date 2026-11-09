---
# A new note in data/catalogues/ named <slug> (lowercase, hyphens). The file name is the slug.
# Fields: src/bookworm/modules/directory/schemas.py (CatalogueRecord).
# Check with `make check-records`. Skill: add-catalogue.
name: Example Catalogue
system: unknown            # vufind | aleph | koha | janium | custom | unknown
system_version: null
base_url: https://catalogue.example.org
automation: unknown        # allowed | disallowed | unknown (robots.txt and terms)
robots_checked_on: null    # YYYY-MM-DD
min_seconds_between_requests: 2.0
access: []                 # in the order to try, e.g.
#  - adapter: vufind.api
#    options: {}
verification:
  status: unverified       # verified | inferred | unverified
  checked_on: null
  source: null
---

What the catalogue is, how it behaves, what was tried and what was seen.
Link example records and searches.

## Libraries in this catalogue

```dataview
TABLE WITHOUT ID
  file.link AS "Library",
  alcaldia AS "Alcaldía",
  catalogue_location AS "Code here",
  verification.status AS "Verified"
FROM "data/libraries"
WHERE catalogue = this.file.name
SORT file.name ASC
```
