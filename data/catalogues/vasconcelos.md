---
name: Biblioteca Vasconcelos catalogue
system: unknown
base_url: https://bibliotecavasconcelos.gob.mx
automation: unknown
access: []
verification:
  status: unverified
  source: README landscape table
---

Web UI only: search by author, title, subject or keyword. Automated fetches
were blocked when tried. Likely needs a browser adapter (`vasconcelos.browser`)
once robots.txt and the terms are checked.

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
