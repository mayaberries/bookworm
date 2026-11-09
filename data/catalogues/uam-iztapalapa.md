---
name: UAM Iztapalapa VuFind
system: vufind
base_url: https://biblioteca.izt.uam.mx/vufind
automation: unknown
access: []
verification:
  status: unverified
  source: README landscape table
---

- Example holdings page: <https://biblioteca.izt.uam.mx/vufind/Record/musev2_2208/Holdings?lng=en>

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
