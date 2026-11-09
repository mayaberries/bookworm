---
name: Nautilo (Biblioteca Nacional de México)
system: vufind
base_url: https://nautilo.iib.unam.mx
automation: unknown
access: []
verification:
  status: inferred
  source: README landscape table (page verified; VuFind inferred from the /Record/<id> pattern)
---

Record pages show call number and copy availability. The software isn't
confirmed: the `/Record/<id>` URL pattern suggests VuFind.

- Example record: <https://nautilo.iib.unam.mx/Record/000587809>

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
