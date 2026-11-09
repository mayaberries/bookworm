---
name: Biblioteca de México catalogue
system: unknown
base_url: https://bibliotecademexico.gob.mx
automation: disallowed
access: []
verification:
  status: unverified
  source: README landscape table
---

Web UI only (Base / Método / Término form; results open in a new tab).
Possibly Aleph, per an older UNAM thesis.

**robots.txt blocks automated access**, so `automation: disallowed`: bookworm
never queries it and lookups say to search it by hand. Set `robots_checked_on`
the next time it's checked.

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
