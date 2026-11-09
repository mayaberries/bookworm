---
# A new note in data/libraries/ named <slug> (lowercase, hyphens). The file name is the slug.
# Fields: src/bookworm/modules/directory/schemas.py (LibraryRecord).
# Check with `make check-records`. Skill: add-library.
name: Example Library
kind: public               # public | national | academic | specialized | other
alcaldia: null             # e.g. Cuauhtémoc (the 16 names in Alcaldia)
address: null
contact:
  phone: null
  email: null
  website: null
catalogue: null            # a slug in data/catalogues/, or null: no online catalogue
catalogue_location: null   # how that catalogue names this library, if it's shared
lending: unknown           # public | members_only | on_site_only | unknown
interlibrary_loan: []      # library slugs
verification:
  status: unverified       # verified | inferred | unverified
  checked_on: null
  source: null
tags: []
---

Opening hours, how to get a card, anything a visitor or the next maintainer
should know.
